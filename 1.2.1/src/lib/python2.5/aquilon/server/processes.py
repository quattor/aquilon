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
import re
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE

from twisted.python import log

from aquilon.exceptions_ import ProcessException, AquilonError
from aquilon.config import Config


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
            log.msg("Error notifying %s: %s" % (host, e))


class DSDBRunner(object):
    # Any "new" object will have all the same info as any other.
    __shared_state = {}

    ip_not_defined_re = re.compile("Host with IP address [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3} is not defined")

    def __init__(self):
        self.__dict__ = self.__shared_state
        if hasattr(self, "config"):
            return
        self.config = Config()

    def getenv(self):
        if (self.config.has_option("broker", "dsdb_use_test") and
                self.config.getboolean("broker", "dsdb_use_test")):
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def add_host(self, dbhost):
        for interface in dbhost.machine.interfaces:
            if not interface.boot:
                continue
            self.add_host_details(dbhost.fqdn, interface.ip,
                    interface.name, interface.mac)
            return
        raise ArgumentError("No boot interface found for host to add to dsdb.")

    def add_host_details(self, fqdn, ip, name, mac):
        out = run_command([self.config.get("broker", "dsdb"),
                "add", "host", "-host_name", fqdn,
                "-ip_address", ip, "-status", "aq",
                "-interface_name", name, "-ethernet_address", mac],
                env=self.getenv())
        return

    def delete_host_details(self, ip):
        try:
            out = run_command([self.config.get("broker", "dsdb"),
                    "delete", "host", "-ip_address", ip],
                    env=self.getenv())
        except ProcessException, e:
            if e.out and self.ip_not_defined_re.search(e.out):
                log.msg("DSDB did not have a host with this IP address, proceeding with aqdb command.")
                return
            raise
        return

    def delete_host(self, dbhost):
        for interface in dbhost.machine.interfaces:
            if not interface.boot:
                continue
            self.delete_host_details(interface.ip)
            return
        raise ArgumentError("No boot interface found for host to delete from dsdb.")

    def update_host(self, dbhost, oldinfo):
        """This gets tricky.  On a basic level, we want to remove the
        old information from dsdb and then re-add it.

        If the removal of the old fails, check to see why.  If the
        entry was already missing, continue.  [This check happens as
        part of the delete_host_details() method.]  If the command
        fails otherwise, punt back to the caller.

        If both succeed, great, continue on.

        If removal succeeds, but adding fails, try to re-add the old
        info, and then pass the failure back to the user.  (Hopefully
        just the original failure, but possibly both.)
        """
        self.delete_host_details(oldinfo["ip"])
        try:
            self.add_host(dbhost)
        except ProcessException, pe1:
            log.msg("Failed adding new information to dsdb, attempting to restore old info.")
            try:
                self.add_host_details(dbhost.fqdn, oldinfo["ip"],
                        oldinfo["name"], oldinfo["mac"])
            except ProcessException, pe2:
                # FIXME: Add details.
                raise AquilonError("DSDB is now in an inconsistent state.  Removing old information succeeded, but cannot add new information.")
            log.msg("Restored old info, re-raising the problem with the add.")
            raise pe1
        return


#if __name__=='__main__':
