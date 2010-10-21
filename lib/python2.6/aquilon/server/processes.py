# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Handling of external processes for the broker happens here.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""


import os
import re
import errno
import logging
from subprocess import Popen, PIPE
from tempfile import mkstemp
from threading import Thread

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import (ProcessException, AquilonError, ArgumentError,
                                 InternalError)
from aquilon.config import Config
from aquilon.server.locks import lock_queue, CompileKey

LOGGER = logging.getLogger('aquilon.server.processes')


class StreamLoggerThread(Thread):
    """Helper class for streaming output as it becomes available."""
    def __init__(self, logger, loglevel, process, stream):
        self.logger = logger
        self.loglevel = loglevel
        self.process = process
        self.stream = stream
        self.buffer = []
        Thread.__init__(self)

    def run(self):
        while True:
            data = self.stream.readline()
            if data == '' and (self.stream.closed or
                               self.process.poll() != None):
                break
            if data != '':
                self.buffer.append(data)
                # This log output will appear in the server logs without
                # correct channel information.  We will re-log it separately
                # and with the correct info.
                self.logger.log(self.loglevel, data.rstrip())


def run_command(args, env=None, path=".",
                logger=LOGGER, loglevel=logging.INFO):
    '''Run the specified command (args should be a list corresponding to ARGV).

    Returns any output (stdout only).  If the command fails, then
    ProcessException will be raised.  To pass the output back to the client
    pass in a logger and specify loglevel as CLIENT_INFO.
    '''
    if env:
        shell_env = env.copy()
    else:
        shell_env = {}

    # Make sure that environment is properly kerberized.
    for envname, envvalue in os.environ.items():
        # AQTEST<something> is used by the testsuite
        if envname.startswith("KRB") or envname.startswith("AQTEST"):
            shell_env[envname] = envvalue

    # Add a default value for the PATH.
    for envname in ["PATH"]:
        if envname not in shell_env and envname in os.environ:
            shell_env[envname] = os.environ[envname]

    # Force any arguments to be strings... takes care of unicode from
    # the database.
    command_args = [str(arg) for arg in args]

    simple_command = " ".join(command_args)
    logger.info("run_command: %s" % simple_command)

    p = Popen(args=command_args, stdin=None, stdout=PIPE, stderr=PIPE,
              cwd=path, env=shell_env)
    out_thread = StreamLoggerThread(logger, loglevel, p, p.stdout)
    err_thread = StreamLoggerThread(logger, loglevel, p, p.stderr)
    out_thread.start()
    err_thread.start()
    out_thread.join()
    err_thread.join()
    p.wait()
    if p.returncode >= 0:
        logger.info("command `%s` exited with return code %d" %
                    (simple_command, p.returncode))
    else:  # pragma: no cover
        logger.info("command `%s` exited with signal %d" %
                    (simple_command, -p.returncode))
    out = "".join(out_thread.buffer)
    if out:
        logger.info("command `%s` stdout: %s" % (simple_command, out))
    err = "".join(err_thread.buffer)
    if err:
        logger.info("command `%s` stderr: %s" % (simple_command, err))

    if p.returncode != 0:
        raise ProcessException(command=simple_command, out=out, err=err,
                               code=p.returncode)
    return out

def run_git(args, env=None, path=".",
            logger=LOGGER, loglevel=logging.INFO):
    config = Config()
    if env:
        git_env = env.copy()
    else:
        git_env = {}
    env_path = git_env.get("PATH", os.environ.get("PATH", ""))
    git_env["PATH"] = "%s:%s" % (config.get("broker", "git_path"), env_path)
    if isinstance(args, list):
        git_args = args[:]
        if git_args[0] != "git":
            git_args.insert(0, "git")
    else:
        git_args = ["git", args]

    return run_command(git_args, env=git_env, path=path,
                       logger=logger, loglevel=loglevel)

def remove_dir(dir, logger=LOGGER):
    """Remove a directory.  Could have been implemented as a call to rm -rf."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                thisfile = os.path.join(root, name)
                os.remove(thisfile)
            except OSError, e:
                logger.info("Failed to remove '%s': %s" % (thisfile, e))
        for name in dirs:
            try:
                thisdir = os.path.join(root, name)
                os.rmdir(thisdir)
            except OSError, e:
                # If this 'directory' is a symlink, the rmdir command
                # will fail.  Try to remove it as a file.  If this
                # fails, report the original error.
                try:
                    os.remove(thisdir)
                except OSError, e1:
                    logger.info("Failed to remove '%s': %s" % (thisdir, e))
    try:
        os.rmdir(dir)
    except OSError, e:
        logger.info("Failed to remove '%s': %s" % (dir, e))
    return

def write_file(filename, content, mode=None, logger=LOGGER):
    """Atomically write content into the specified filename.

    The content is written into a temp file in the same directory as
    filename, and then swapped into place with rename.  This assumes
    that both the file and the directory can be written to by the
    broker.  The same directory was used instead of a temporary
    directory because atomic swaps are generally only available when
    the source and the target are on the same filesystem.

    If mode is set, change permissions on the file (newly created or
    pre-existing) to the new mode.  If unset and the file exists, the
    current permissions will be kept.  If unset and the file is new,
    the default is 0644.

    This method may raise OSError if any of the OS-related methods
    (creating the temp file, writing to it, correcting permissions,
    swapping into place) fail.  The method will attempt to remove
    the temp file if it had been created.

    """
    if mode is None:
        try:
            old_mode = os.stat(filename).st_mode
        except OSError, e:
            old_mode = 0644
    (dirname, basename) = os.path.split(filename)
    (fd, fpath) = mkstemp(prefix=basename, dir=dirname)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        if mode is None:
            os.chmod(fpath, old_mode)
        else:
            os.chmod(fpath, mode)
        os.rename(fpath, filename)
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)

def read_file(path, filename, logger=LOGGER):
    fullfile = os.path.join(path, filename)
    try:
        return open(fullfile).read()
    except OSError, e:
        raise AquilonError("Could not read contents of %s: %s"
                % (fullfile, e))

def remove_file(filename, logger=LOGGER):
    try:
        os.remove(filename)
    except OSError, e:
        if e.errno != errno.ENOENT:
            logger.info("Could not remove file '%s': %s" % (filename, e))

def cache_version(config, logger=LOGGER):
    """Try to determine the broker version by examining the path
    to this source file.  If this file path matches
    /aquilon/PROJ/aqd/<version>/ (likely /ms/dist) or
    /aquilon/aqd/<version>/ (likely /ms/dev) then use <version>.

    Otherwise, run git describe to get the most recent tag.

    """

    if config.has_option("broker", "version"):
        return

    version_re = re.compile(r'/aquilon(?:/PROJ)?/aqd/([^/]+)/')
    m = version_re.search(__file__)
    if m and m.group(1) != "lib" and m.group(1) != "bin":
        config.set("broker", "version", m.group(1))
        return

    try:
        out = run_git("describe", logger=logger,
                      path=config.get("broker", "srcdir"))
        config.set("broker", "version", out.strip())
    except ProcessException, e:
        logger.info("Could not run git describe to get version: %s" % e)
        config.set("broker", "version", "Unknown")

def sync_domain(dbdomain, logger=LOGGER, locked=False):
    """Update templates on disk to match contents of branch in template-king.

    If this domain is tracking another, first update the branch in
    template-king with the latest from the tracking branch.  Also save
    the current (previous) commit as a potential rollback point.

    """
    config = Config()
    session = object_session(dbdomain)
    kingdir = config.get("broker", "kingdir")
    domaindir = os.path.join(config.get("broker", "domainsdir"), dbdomain.name)
    git_env = {"PATH":"%s:%s" % (config.get("broker", "git_path"),
                                 os.environ.get("PATH", ""))}
    if dbdomain.tracked_branch:
        # Might need to revisit if using this helper from rollback...
        run_command(["git", "push", ".",
                     "%s:%s" % (dbdomain.tracked_branch.name, dbdomain.name)],
                    path=kingdir, env=git_env, logger=logger)
    run_command(["git", "fetch"], path=domaindir, env=git_env, logger=logger)
    if dbdomain.tracked_branch:
        out = run_command(["git", "log", "HEAD", "-n", "1",
                           "--format=format:%H"],
                          path=domaindir, env=git_env, logger=logger)
        rollback_commit = out.strip()
    try:
        if not locked:
            key = CompileKey(domain=dbdomain.name, logger=logger)
            lock_queue.acquire(key)
        run_command(["git", "reset", "--hard", "origin/%s" % dbdomain.name],
                    path=domaindir, env=git_env, logger=logger)
    finally:
        if not locked:
            lock_queue.release(key)
    if dbdomain.tracked_branch:
        dbdomain.rollback_commit = rollback_commit
        session.add(dbdomain)


IP_NOT_DEFINED_RE = re.compile("Host with IP address "
                               "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
                               " is not defined")

class DSDBRunner(object):

    def __init__(self, logger=LOGGER):
        self.config = Config()
        self.logger = logger
        self.dsdb = self.config.get("broker", "dsdb")
        self.location_sync = self.config.getboolean(
            "broker", "dsdb_location_sync")

    def getenv(self):
        if self.config.getboolean("broker", "dsdb_use_testdb"):
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def add_city(self, city, country, fullname):
        cmd = [self.dsdb, "add_city_aq", "-city_symbol", city,
               "-country_symbol", country, "-city_name", fullname]
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    def del_city(self, city):
        cmd = [self.dsdb, "delete_city_aq", "-city", city]
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    def add_building(self, building, city, building_addr):
        cmd = [self.dsdb, "add_building_aq", "-building_name", building,
               "-city", city, "-building_addr", building_addr]
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    def del_building(self, building):
        cmd = [self.dsdb, "delete_building_aq", "-building", building]
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    def add_host(self, dbinterface):
        session = object_session(dbinterface)
        primary = dbinterface.hardware_entity.fqdn
        for addr in dbinterface.all_addresses():
            if not addr.fqdns:
                continue
            if addr.vlan.vlan_id == 0 and not addr.label:
                mac = dbinterface.mac
            else:
                mac = None
            self.add_host_details(addr.fqdns[0], addr.ip, addr.logical_name,
                                  mac, primary=primary)

    def add_host_details(self, fqdn, ip, name, mac, primary=None):
        # DSDB does not accept '/' as valid in an interface name.
        command = [self.config.get("broker", "dsdb"),
                    "add", "host", "-host_name", fqdn,
                    "-ip_address", ip, "-status", "aq"]
        if name:
            interface = str(name).replace('/', '_')
            command.extend(["-interface_name", interface])
        if mac:
            command.extend(["-ethernet_address", mac])
        if primary and primary != fqdn:
            command.extend(["-primary_host_name", primary])
        out = run_command(command,env=self.getenv())
        return

    def update_host_mac(self, fqdn, mac):
        command = [self.config.get("broker", "dsdb"),
                   "update", "host", "-host_name", fqdn, "-status", "aq",
                   "-ethernet_address", mac]
        return run_command(command, env=self.getenv(), logger=self.logger)

    def delete_host_details(self, ip):
        try:
            out = run_command([self.config.get("broker", "dsdb"),
                    "delete", "host", "-ip_address", ip],
                    env=self.getenv())
        except ProcessException, e:
            if e.out and IP_NOT_DEFINED_RE.search(e.out):
                self.logger.info("DSDB did not have a host with this IP "
                                 "address, proceeding with aqdb command.")
                return
            raise
        return

    # Not generally useful, because we have already run session.delete()
    # on the dbhost object.
#    def delete_host(self, dbhost):
#        for interface in dbhost.hardware_entity.interfaces:
#            if not interface.boot:
#                continue
#            self.delete_host_details(interface.ip)
#            return
#        raise ArgumentError("No boot interface found for host to delete from dsdb.")

    @classmethod
    def snapshot_hw(cls, dbhw_ent):
        """
        Make a snapshot of the interface parameters.

        update_host() will use this snapshot to decide what has changed and
        what DSDB commands have to be executed.
        """

        status = {}

        # If the hw does not have a primary name with an IP, then it should not
        # be in DSDB
        if not dbhw_ent or not dbhw_ent.primary_ip:
            return status

        primary = dbhw_ent.fqdn

        for iface in dbhw_ent.interfaces:
            for addr in iface.all_addresses():
                if addr.fqdns:
                    fqdn = addr.fqdns[0]
                else:
                    continue

                # The MAC must be unique in DSDB, so only set it for the first
                # address on the native VLAN
                if addr.vlan.vlan_id == 0 and not addr.label:
                    mac = iface.mac
                else:
                    mac = None
                key = '%s:%s' % (primary, addr.logical_name)
                status[key] = {'name': addr.logical_name,
                               'mac': mac,
                               'ip': addr.ip,
                               'fqdn': fqdn,
                               'primary': primary}
        return status

    def update_host(self, dbhw_ent, oldinfo):
        """Update a dsdb host entry.

        The calling code (the aq update_interface command) treats the
        hostname and interface name as unchanging.  There is an
        update_host dsdb command that lets the mac address (and comments,
        if we kept them) change.

        Any other changes have to be done by removing the old DSDB
        entry and adding a new one.

        """
        newinfo = self.snapshot_hw(dbhw_ent)

        if not oldinfo:
            oldinfo = {}

        deletes = []
        adds = []
        mac_update = None

        # Construct the list of operations
        for key, attrs in oldinfo.items():
            if key not in newinfo:
                deletes.append(attrs)
            elif attrs['ip'] != newinfo[key]['ip'] or \
                    attrs['primary'] != newinfo[key]['primary']:
                deletes.append(attrs)
                adds.append(newinfo[key])
            elif attrs['mac'] != newinfo[key]['mac']:
                mac_update = newinfo[key]
        for key, attrs in newinfo.items():
            if key not in oldinfo:
                adds.append(attrs)

        rollback_adds = []
        rollback_deletes = []
        try:
            for attrs in deletes:
                self.delete_host_details(attrs['ip'])
                rollback_deletes.append(attrs)
            for attrs in adds:
                self.add_host_details(attrs['fqdn'], attrs['ip'],
                                      attrs['name'], attrs['mac'],
                                      attrs['primary'])
                rollback_adds.append(attrs)
            if mac_update:
                self.update_host_mac(mac_update['fqdn'], mac_update['mac'])
        except ProcessException, e:
            self.logger.info("Failed updating DSDB entry for {0:l}: "
                             "{1!s}".format(dbhw_ent, e))
            rollback_failures = []
            for attrs in rollback_adds:
                try:
                    self.delete_host_details(attrs['ip'])
                except Exception, err:
                    rollback_failures.append(str(err))
            for attrs in rollback_deletes:
                try:
                    self.add_host_details(attrs['fqdn'], attrs['ip'],
                                          attrs['name'], attrs['mac'],
                                          attrs['primary'])
                except Exception, err:
                    rollback_failures.append(str(err))
            msg = "DSDB update failed: %s" % e
            if rollback_failures:
                msg += "\n\nRollback also failed, DSDB state is inconsistent:" + \
                        "\n".join(rollback_failures)
            raise AquilonError(msg)
        return

    def add_dns_domain(self, dns_domain, comments):
        try:
            out = run_command([self.config.get("broker", "dsdb"),
                    "show", "dns_domains", "-domain_name", dns_domain],
                    env=self.getenv())
        except ProcessException, e:
            self.logger.info("The DNS domain %s does not exist in DSDB, "
                             "adding it." % dns_domain)
        else:
            self.logger.info("The DNS domain %s already exists in DSDB, "
                             "continuing." % dns_domain)
            return

        if not comments:
            comments = ""
        out = run_command([self.config.get("broker", "dsdb"),
                "add", "dns_domain", "-domain_name", dns_domain,
                "-comments", comments], env=self.getenv())
        return

    def delete_dns_domain(self, dns_domain):
        try:
            out = run_command([self.config.get("broker", "dsdb"),
                    "delete", "dns_domain", "-domain_name", dns_domain],
                    env=self.getenv())
        except ProcessException, e:
            self.logger.info("Encountered a problem removing the DNS domain "
                             "%s from DSDB, continuing: %s" % (dns_domain, e))
        else:
            self.logger.info("Removed DNS domain %s from DSDB." % dns_domain)
        return

    primary_re = re.compile(r'^Primary Name:\s*\b([-\w]+)\b$', re.M)
    node_re = re.compile(r'^Node:\s*\b([-\w]+)\b$', re.M)
    dns_re = re.compile(r'^DNS Domain:\s*\b([-\w\.]+)\b$', re.M)
    state_re = re.compile(r'^State:\s*\b(\d+)\b$', re.M)

    def show_host(self, hostname):
        (short, dot, dns_domain) = hostname.partition(".")
        fields = {}
        if not dot:
            fields["fqdn"] = short + ".ms.com"
            fields["dsdb_lookup"] = short
        elif not dns_domain:
            fields["fqdn"] = short + "ms.com"
            fields["dsdb_lookup"] = short
        elif dns_domain != "ms.com":
            fields["fqdn"] = hostname
            fields["dsdb_lookup"] = hostname
        else:
            fields["fqdn"] = hostname
            fields["dsdb_lookup"] = short

        out = run_command([self.config.get("broker", "dsdb"),
                "show", "host", "-host_name", fields["dsdb_lookup"]],
                env=self.getenv())
        primary = self.primary_re.search(out)
        node = self.node_re.search(out)
        dns = self.dns_re.search(out)
        state = self.state_re.search(out)
        fields["primary_name"] = primary and primary.group(1) or None
        fields["node"] = node and node.group(1) or None
        fields["dns"] = dns and dns.group(1) or None
        if state:
            fields["state"] = int(state.group(1))
        else:
            fields["state"] = None
        return fields
