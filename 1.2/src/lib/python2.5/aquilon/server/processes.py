#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Handling of external processes for the broker happens here.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""

import os
import time
import socket
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE

from twisted.python import log

from aquilon.exceptions_ import ProcessException, AquilonError

CCM_NOTIF = 1
CDB_NOTIF = 2

notification_types = {
        CCM_NOTIF : "ccm",
        CDB_NOTIF : "cdb"
}

def run_command(args, env=None, path="."):
    if env:
        shell_env = env.copy()
    else:
        shell_env = {}

    # Make sure that environment is properly kerberized.
    for envname, envvalue in os.environ.items():
        if not envname.startswith("KRB"):
            continue
        shell_env[envname] = envvalue

    # Force any arguments to be strings... takes care of unicode from
    # the database.
    command_args = [str(arg) for arg in args]

    p = Popen(args=command_args, stdout=PIPE, stderr=PIPE, cwd=path,
            env=shell_env)
    (out, err) = p.communicate()

    simple_command = " ".join(command_args)
    if p.returncode >= 0:
        log.msg("command `%s` exited with return code %d" %
                (simple_command, p.returncode))
    else:
        log.msg("command `%s` exited with signal %d" %
                (simple_command, -p.returncode))
    if out:
        log.msg("command `%s` stdout: %s" % (simple_command, out))
    if err:
        log.msg("command `%s` stderr: %s" % (simple_command, err))
    if p.returncode != 0:
        raise ProcessException(command=simple_command, out=out, err=err,
                code=p.returncode)
    return out


def remove_dir(dir):
    """Remove a directory.  Could have been implemented as a call to rm -rf."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except OSError, e:
                log.err(e)
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError, e:
                log.err(e)
    try:
        os.rmdir(dir)
    except OSError, e:
        log.err(e)
    return

def write_file(filename, content):
    # FIXME: Wrap errors in a ProcessException?
    f = open(filename, 'w')
    f.write(content)
    f.close()

def read_file(path, filename):
    fullfile = os.path.join(path, filename)
    try:
        return open(fullfile).read()
    except OSError, e:
        raise AquilonError("Could not read contents of %s: %s"
                % (fullfile, e))

def remove_file(filename):
    try:
        os.remove(filename)
    except OSError, e:
        log.msg("Could not remove file '%s': %s" % (filename, e))

# This functionality (build_index, send_notification) may be better
# suited in a different module.  Here for now, though.
def build_index(profilesdir):
    ''' compare the mtimes of everything in profiledir against
    and index file (profiles-info.xml). Produce a new index
    and send out notifications to everything that's been updated
    and to all subscribers of the index (bootservers currently)
    '''

    profile_index = "profiles-info.xml"

    old_host_index = {}
    index_path = os.path.join(profilesdir, profile_index)
    if os.path.exists(index_path):
        try:
            tree = ET.parse(index_path)
            for profile in tree.getiterator("profile"):
                if (profile.text and profile.attrib.has_key("mtime")):
                    host = profile.text.strip()
                    if host:
                        if host.endswith(".xml"):
                            host = host[:-4]
                        old_host_index[host] = int(profile.attrib["mtime"])
                        #log.msg("Stored %d for %s" % (old_host_index[host],
                        #    host))
        except Exception, e:
            log.msg("Error processing %s, continuing: %s" % (index_path, e))

    host_index = {}
    modified_index = {}
    for profile in os.listdir(profilesdir):
        if profile == profile_index:
            continue
        if not profile.endswith(".xml"):
            continue
        host = profile[:-4]
        host_index[host] = os.path.getmtime(
                os.path.join(profilesdir, profile))
        #log.msg("Found profile for %s with mtime %d"
        #        % (host, host_index[host]))
        if (old_host_index.has_key(host)
                and host_index[host] > old_host_index[host]):
            #log.msg("xml for %s has a newer mtime, will notify" % host)
            modified_index[host] = host_index[host]

    content = []
    content.append("<?xml version='1.0' encoding='utf-8'?>")
    content.append("<profiles>")
    for host, mtime in host_index.items():
        content.append("<profile mtime='%d'>%s.xml</profile>"
                % (mtime, host))
    content.append("</profiles>")

    f = open(index_path, 'w')
    f.write("\n".join(content))
    f.close()

    # Read cdb.conf on demand so that it can be updated while the
    # broker is running.
    server_modules = []
    try:
        f = open("/etc/cdb.conf")
        for line in f.readlines():
            line = line.strip()
            if not line.startswith("server_module"):
                continue
            servers = line.split()
            for server in servers[1:]:
                if server.strip():
                    server_modules.append(server)
        f.close()
    except Exception, e:
        log.msg("Could not retrieve list of server_modules: %s" % e)

    send_notification(CCM_NOTIF, modified_index.keys())
    send_notification(CDB_NOTIF, server_modules)

def send_notification(type, machines):
    '''send CDP notification messages to a list of hosts. This
    are sent synchronously, but we don't wait (or care) for any
    reply, so it shouldn't be a problem.
    type should be CCM_NOTIF or CDB_NOTIF
    '''
    packet = notification_types[type] + "\0" + str(int(time.time()))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        port = socket.getservbyname("cdp")
    except:
        port = 7777

    for host in machines:
        try:
            log.msg("Sending %s notification to %s"
                    % (notification_types[type], host))
            ip = socket.gethostbyname(host)
            sock.sendto(packet, (ip, port))
        except Exception, e:
            log.msg("Error notifying %s: %s", host, e)

### Old code follows to deal with dsdb that needs to be reimplemented.
###
#    # Hack to deal with IPs already in dsdb.  In theory, we *want* dsdb to
#    # tell us when there are conflicts, but right now it isn't helping.
#    def eb_ignore_already_defined(self, failure):
#        failure.trap(ProcessException)
#        if failure.value.out and failure.value.out.find("already defined") >= 0:
#            log.msg("DSDB check failed, continuing anyway!")
#            return True
#        return failure
#
#    # Expects to be run after dbaccess.verify_add_host.
#    def add_host(self, (short, dbdns_domain, dbmachine), dsdb, **kwargs):
#        """add_host only adds the primary interface (marked boot) to dsdb."""
#        env = {"DSDB_USE_TESTDB": "true"}
#        for interface in dbmachine.interfaces:
#            if not interface.boot:
#                continue
#            d = self.run_shell_command(True,
#                """%s add host -host_name "%s" -dns_domain "%s" -ip_address "%s" -status aq -interface_name "%s" -ethernet_address "%s" """
#                % (dsdb, short, dbdns_domain.name, interface.ip,
#                interface.name, interface.mac),
#                env=env)
#            # FIXME: This should not be used...
#            d = d.addErrback(self.eb_ignore_already_defined)
#            d = d.addErrback(self.eb_detailed_command)
#            return d
#        raise ArgumentError("No boot interface found for host to remove from dsdb.")
#    
#    # Hack to deal with IPs already in dsdb.  In theory, we *want* dsdb to
#    # tell us when there are conflicts, but right now it isn't helping.
#    def eb_ignore_node_host(self, failure):
#        failure.trap(ProcessException)
#        if failure.value.out and failure.value.out.find(
#                "Run dsdb_delete_node_host") >= 0:
#            log.msg("DSDB check failed, continuing anyway!")
#            return True
#        return failure
#
#    # Expects to be run after dbaccess.verify_del_host.
#    def del_host(self, result, dsdb, **kwargs):
#        """del_host only removes the primary interface (boot) from dsdb."""
#
#        dbmachine = result
#        env = {"DSDB_USE_TESTDB": "true"}
#        for interface in dbmachine.interfaces:
#            if not interface.boot:
#                continue
#            d = self.run_shell_command(True,
#                """%s delete host -ip_address "%s" """
#                % (dsdb, interface.ip),
#                env=env)
#            # FIXME: This should not be used...
#            d = d.addErrback(self.eb_ignore_node_host)
#            d = d.addErrback(self.eb_detailed_command)
#            return d
#        raise ArgumentError("No boot interface found for host to add to dsdb.")


#if __name__=='__main__':
