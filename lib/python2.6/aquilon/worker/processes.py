# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
import gzip
from subprocess import Popen, PIPE
from tempfile import mkstemp
from threading import Thread
from cStringIO import StringIO
from functools import wraps

from sqlalchemy.orm.session import object_session
import yaml

from aquilon.exceptions_ import (ProcessException, AquilonError, ArgumentError,
                                 InternalError)
from aquilon.config import Config
from aquilon.worker.locks import lock_queue, CompileKey

LOGGER = logging.getLogger(__name__)


class StreamLoggerThread(Thread):
    """Helper class for streaming output as it becomes available."""
    def __init__(self, logger, loglevel, process, stream, filterre=None):
        self.logger = logger
        self.loglevel = loglevel
        self.process = process
        self.stream = stream
        self.filterre = filterre
        self.buffer = []
        Thread.__init__(self)

    def run(self):
        while True:
            data = self.stream.readline()
            if data == '' and (self.stream.closed or
                               self.process.poll() != None):
                break
            if data != '':
                if self.filterre and not self.filterre.search(data):
                    continue
                self.buffer.append(data)
                # This log output will appear in the server logs without
                # correct channel information.  We will re-log it separately
                # and with the correct info.
                self.logger.log(self.loglevel, data.rstrip())


def run_command(args, env=None, path=".", logger=LOGGER, loglevel=logging.INFO,
                filterre=None, input=None):
    '''Run the specified command (args should be a list corresponding to ARGV).

    Returns any output (stdout only).  If the command fails, then
    ProcessException will be raised.  To pass the output back to the client
    pass in a logger and specify loglevel as CLIENT_INFO.

    To reduce the captured output, pass in a compiled regular expression
    with the filterre keyword argument.  Any output lines on stdout will
    only be kept if filterre.search() finds a match.

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

    if input:
        proc_stdin = PIPE
        logger.info("command `%s` stdin: %s" % (simple_command, input))
    else:
        proc_stdin = None

    p = Popen(args=command_args, stdin=proc_stdin, stdout=PIPE, stderr=PIPE,
              cwd=path, env=shell_env)
    out_thread = StreamLoggerThread(logger, loglevel, p, p.stdout,
                                    filterre=filterre)
    err_thread = StreamLoggerThread(logger, loglevel, p, p.stderr)
    out_thread.start()
    err_thread.start()
    if proc_stdin:
        p.stdin.write(input)
        p.stdin.close()
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
        filter_msg = "filtered " if filterre else ""
        logger.info("command `%s` %sstdout: %s" %
                    (simple_command, filter_msg, out))
    err = "".join(err_thread.buffer)
    if err:
        logger.info("command `%s` stderr: %s" % (simple_command, err))

    if p.returncode != 0:
        raise ProcessException(command=simple_command, out=out, err=err,
                               code=p.returncode, filtered=bool(filterre))
    return out

def run_git(args, env=None, path=".",
            logger=LOGGER, loglevel=logging.INFO, filterre=None):
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
                       logger=logger, loglevel=loglevel, filterre=filterre)

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

def write_file(filename, content, mode=None, logger=LOGGER, compress=None):
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

    If the compress keyword is passed, the content is compressed in
    memory before writing.  The only compression currently supported
    is gzip.

    """
    if compress == 'gzip':
        config = Config()
        buffer = StringIO()
        compress = config.getint('broker', 'gzip_level')
        zipper = gzip.GzipFile(filename, 'wb', compress, buffer)
        zipper.write(content)
        zipper.close()
        content = buffer.getvalue()
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
    run_command(["git", "fetch", "--prune"], path=domaindir, env=git_env, logger=logger)
    if dbdomain.tracked_branch:
        out = run_command(["git", "rev-list", "-n", "1", "HEAD"],
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


IP_NOT_DEFINED_RE = re.compile(r"Host with IP address "
                               r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
                               r" is not defined")

BUILDING_NOT_FOUND = re.compile(r"bldg [a-zA-Z0-9]{2} doesn't exists")

CAMPUS_NOT_FOUND = re.compile(r"campus [a-zA-Z0-9]{2} doesn't exist")

DNS_DOMAIN_NOT_FOUND = re.compile (r"DNS domain ([-\w\.\d]+) doesn't exists")

DNS_DOMAIN_EXISTS = re.compile(r"DNS domain [-\w\.\d]+ already defined")


def rollback_decorator(fn):
    @wraps(fn)
    def tracer(*args, **kwargs):
        try:
            dself = args[0]
            fn(*args, **kwargs)
            if dself.action:
                dself.logger.info("Action: " + dself.action)
            dself.action = None

            if "revert" in kwargs and kwargs["revert"] is not None:
                dself.rollbacks.append(kwargs["revert"])
            else:
                dself.logger.debug("%s.%s called with no rollback info." %
                                   (dself.__class__.__name__, fn.__name__))
        except AquilonError, err:
            failed_action = dself.action
            dself.logger.client_info("Rolling back: " + failed_action)
            dself.rollback()
            raise ArgumentError("Error while " + failed_action + ": %s" % err)

    return tracer

class DSDBRunner(object):

    def __init__(self, logger=LOGGER):
        config = Config()
        self.logger = logger
        self.dsdb = config.get("broker", "dsdb")
        self.dsdb_use_testdb = config.getboolean("broker", "dsdb_use_testdb")
        self.location_sync = config.getboolean("broker", "dsdb_location_sync")
        self.rollbacks = []
        self.action = None

    def rollback(self):
        self.rollbacks.reverse()
        for r in self.rollbacks:
            (action, args) = (r[0], r[1])
            try:
                action(*args)
            except AquilonError, err:
                self.logger.warn("Error rolling back: %s" % err)

        self.rollbacks = []

    def getenv(self):
        if self.dsdb_use_testdb:
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def run_if_sync(self, cmd):
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    @rollback_decorator
    def add_campus(self, campus, comments):
        self.action = "adding new campus %s to DSDB." % campus

        command = [self.dsdb, "add_campus_aq", "-campus_name", campus]
        if comments:
            command.extend(["-comments", comments])
        self.run_if_sync(command)

    @rollback_decorator
    def del_campus(self, campus):
        self.action = "removing campus %s from DSDB." % campus

        try:
            self.run_if_sync([self.dsdb, "delete_campus_aq", "-campus", campus])
        except ProcessException, e:
            if e.out and CAMPUS_NOT_FOUND.search(e.out):
                self.logger.info("DSDB does not have a campus %s defined, "
                                 "proceeding with aqdb command." % campus)
                return
            raise

    @rollback_decorator
    def add_city(self, city, country, fullname):
        self.action = "adding new city %s to DSDB." % (city)

        self.run_if_sync([self.dsdb, "add_city_aq", "-city_symbol", city,
               "-country_symbol", country, "-city_name", fullname])

    @rollback_decorator
    def update_city(self, city, campus, revert=None):
        self.action = "updating campus of city %s to %s in DSDB." % (city,
                                                                     campus)

        self.run_if_sync([self.dsdb, "update_city_aq", "-city", city,
               "-campus", campus])

    @rollback_decorator
    def del_city(self, city):
        self.action = "removing city %s to DSDB." % (city)
        self.run_if_sync([self.dsdb, "delete_city_aq", "-city", city])

    @rollback_decorator
    def add_campus_building(self, campus, building, revert=None):
        self.action = "adding building %s to campus %s in DSDB." % (building,
                                                               campus)
        cmd = [self.dsdb, "add_campus_building_aq", "-campus_name", campus,
               "-building_name", building]
        if self.location_sync:
            out = run_command(cmd, env=self.getenv(), logger=self.logger)
        else:
            self.logger.debug(
                "Would have called '%s' if location sync was enabled" % cmd)

    @rollback_decorator
    def add_building(self, building, city, building_addr, revert=None):
        self.action = "adding new building %s to DSDB." % building

        self.run_if_sync([self.dsdb, "add_building_aq",
                          "-building_name", building,
                          "-city", city, "-building_addr", building_addr])

    @rollback_decorator
    def del_campus_building(self, campus, building, revert=None):
        self.action = "removing building %s from campus %s in DSDB." % (building,
                                                                   campus)
        self.run_if_sync([self.dsdb, "delete_campus_building_aq",
               "-campus_name", campus, "-building_name", building])

    @rollback_decorator
    def del_building(self, building, revert=None):
        self.action = "removing building %s from DSDB." % building

        try:
            self.run_if_sync([self.dsdb, "delete_building_aq",
                              "-building", building])
        except ProcessException, e:
            if e.out and BUILDING_NOT_FOUND.search(e.out):
                self.logger.info("DSDB does not have a building %s defined, "
                                 "proceeding with aqdb command." % building)
                return
            raise

    @rollback_decorator
    def update_building(self, building, building_addr, revert=None):
        self.action = "set address of building %s to %s in DSDB." % \
            (building, building_addr)
        self.run_if_sync([self.dsdb, "update_building_aq",
                          "-building_name", building,
                          "-building_addr", building_addr])

    def add_host_details(self, fqdn, ip, name, mac, primary=None, comments=None):
        # DSDB does not accept '/' as valid in an interface name.
        command = [self.dsdb, "add_host", "-host_name", fqdn,
                    "-ip_address", ip, "-status", "aq"]
        if name:
            interface = str(name).replace('/', '_').replace(':', '_')
            command.extend(["-interface_name", interface])
        if mac:
            command.extend(["-ethernet_address", mac])
        if primary and str(primary) != str(fqdn):
            command.extend(["-primary_host_name", primary])
        if comments:
            command.extend(["-comments", comments])
        out = run_command(command, env=self.getenv())
        return

    def update_host_details(self, fqdn, mac=None, comments=None):
        command = [self.dsdb, "update_host", "-host_name", fqdn, "-status", "aq"]
        if mac:
            command.extend(["-ethernet_address", mac])
        if comments:
            command.extend(["-comments", comments])
        return run_command(command, env=self.getenv(), logger=self.logger)

    def update_host_ip(self, name, fqdn, ip):
        command = [self.dsdb, "update_aqd_host", "-host_name", fqdn,
                   "-interface_name", name, "-ip_address", ip]
        return run_command(command, env=self.getenv(), logger=self.logger)

    def update_host_name(self,ifname, fqdn, fqdn_new):
        command = [self.dsdb, "update_aqd_host", "-host_name", fqdn,
                   "-interface_name", ifname, "-primary_host_name", fqdn_new]
        return run_command(command, env=self.getenv(), logger=self.logger)

    def delete_host_details(self, ip):
        try:
            out = run_command([self.dsdb, "delete_host", "-ip_address", ip],
                              env=self.getenv())
        except ProcessException, e:
            if e.out and IP_NOT_DEFINED_RE.search(e.out):
                self.logger.info("DSDB did not have a host with this IP "
                                 "address, proceeding with aqdb command.")
                return
            raise
        return

    @classmethod
    def snapshot_hw(cls, dbhw_ent):
        """
        Make a snapshot of the interface parameters.

        update_host() will use this snapshot to decide what has changed and
        what DSDB commands have to be executed.

        Comment handling is a bit complicated, because we have more ways to
        store comments in Aquilon than in DSDB. The rules are:

        - If the interface has a comment, use that.

          Exception: dummy interfaces created by add_switch/add_chassis; we
          don't want to propagate the "Created automatically ..." comment

        - Otherwise take the comment from the hardware entity.

          Exception: management interfaces
        """

        status = {}


        real_primary = dbhw_ent.fqdn

        # We need a stable index for generating virtual interface names for
        # DSDB. Sort the Zebra IPs and use the list index for this purpose.
        # There is an exception though: while renumbering and thus
        # deleting/re-adding the virtual interfaces is generally fine, we do not
        # want to remove the primary IP address. So make sure the primary IP is
        # always the first one.
        zebra_ips = []
        for addr in dbhw_ent.all_addresses():
            if not addr.network.is_internal:
                continue
            if not addr.service_address or \
               addr.service_address.holder.holder_type != 'host' or \
               addr.ip in zebra_ips:
                continue
            zebra_ips.append(addr.ip)
        zebra_ips.sort()
        if dbhw_ent.primary_ip and dbhw_ent.primary_ip in zebra_ips:
            zebra_ips.remove(dbhw_ent.primary_ip)
            zebra_ips.insert(0, dbhw_ent.primary_ip)

        for addr in dbhw_ent.all_addresses():
            if not addr.network.is_internal:
                continue
            if addr.fqdns:
                fqdn = str(addr.fqdns[0])
            else:
                continue

            if addr.interface.interface_type != 'management':
                # TODO: This works for switches, but for hosts we eventually
                # want to propagate dbhwent.host.comments instead of
                # dbhw_ent.comments. On the other hand we have plans to attach
                # Host objects to switches; if we do that, then we may switch to
                # using dbhwent.host.comments unconditionally.
                comments = dbhw_ent.comments
            else:
                # Do not propagate machine comments to managers
                comments = None

            # Zebra: in AQDB the address is assigned to multiple existing
            # interfaces. In DSDB however, we need just a single virtual
            # interface
            if addr.ip in zebra_ips:
                ifname = "le%d" % zebra_ips.index(addr.ip)
            elif addr.service_address:
                continue
            else:
                ifname = addr.logical_name
                if addr.interface.comments and not \
                   addr.interface.comments.startswith("Created automatically"):
                    comments = addr.interface.comments

            # The blind build magic in "add_interface --machine" renames the
            # machine, so we can't use dbhw_ent.label in the key. Renaming e.g.
            # switches also depend on using a key that does not include the
            # label.
            key = '%s:%s' % (dbhw_ent.id, ifname)

            if key in status:
                continue

            if addr.interface.interface_type == "management":
                # Do not use -primary_host_name for the management address
                primary = None
            elif fqdn == real_primary:
                # Do not set the 'primary' key for the real primary name.
                # update_host() uses this hint for issuing the operations in the
                # correct order
                primary = None
            else:
                primary = real_primary

            status[key] = {'name': ifname,
                           'ip': addr.ip,
                           'fqdn': fqdn,
                           'primary': primary,
                           'comments': comments}

            # Exclude the MAC address for aliases
            if addr.label:
                status[key]["mac"] = None
            else:
                status[key]["mac"] = addr.interface.mac
        return status

    def update_host(self, dbhw_ent, oldinfo):
        """Update a dsdb host entry.

        The calling code (the aq update_interface command) treats the
        hostname and interface name (except for zebra hosts!) as unchanging .
        There is an update_host dsdb command that lets the mac address,
        ip address (and comments, if we kept them) change.

        Any other changes have to be done by removing the old DSDB
        entry and adding a new one.

        Please note that in case of zebra interfaces adding a new ip address
        to the same interface may result in adding/removing DSDB entries.
        """
        newinfo = self.snapshot_hw(dbhw_ent)

        if not oldinfo:
            oldinfo = {}

        deletes = []
        adds = []
        updates = []
        ip_updates = []
        hostname_update = None

        # Construct the list of operations
        for key, attrs in oldinfo.items():
            if key not in newinfo:
                deletes.append(attrs)
            elif attrs['primary'] != newinfo[key]['primary'] or attrs['fqdn'] != newinfo[key]['fqdn']:
                deletes.append(attrs)
                adds.append(newinfo[key])
            else:
                if attrs['ip'] != newinfo[key]['ip']:
                    ip_updates.append({"fqdn": attrs['fqdn'],
                                       "name": attrs['name'],
                                       "oldip": attrs['ip'],
                                       "newip": newinfo[key]['ip']})
                if attrs['mac'] != newinfo[key]['mac'] or \
                        attrs['comments'] != newinfo[key]['comments']:
                    update = {'fqdn': attrs['fqdn']}
                    if attrs['mac'] != newinfo[key]['mac']:
                        update['oldmac'] = attrs['mac']
                        update['newmac'] = newinfo[key]['mac']
                    if attrs['comments'] != newinfo[key]['comments']:
                        update['oldcomments'] = attrs['comments']
                        update['newcomments'] = newinfo[key]['comments']
                    updates.append(update)
                if attrs['fqdn'] != newinfo[key]['fqdn']:
                    hostname_update = {"ifname": attrs['name'],
                                       "oldfqdn": attrs['fqdn'],
                                       "newfqdn": newinfo[key]['fqdn']}

        for key, attrs in newinfo.items():
            if key not in oldinfo:
                adds.append(attrs)

        # Add the primary address first, and delete it last. The primary address
        # is identified by having an empty ['primary'] key (this is true for the
        # management address as well, but it does not matter).
        adds.sort(lambda x, y: cmp(x['primary'] or "", y['primary'] or ""))
        deletes.sort(lambda x, y: cmp(x['primary'] or "", y['primary'] or ""), reverse=True)

        rollback_adds = []
        rollback_deletes = []
        rollback_updates = []
        rollback_ip_updates = []
        try:
            for attrs in deletes:
                self.delete_host_details(attrs['ip'])
                rollback_deletes.append(attrs)

            for attrs in updates:
                self.update_host_details(attrs['fqdn'],
                                         mac=attrs.get('newmac', None),
                                         comments=attrs.get('newcomments', None))
                rollback_updates.append({'fqdn': attrs['fqdn'],
                                         'mac': attrs.get('oldmac', None),
                                         'comments': attrs.get('oldcomments', None)})
            for attrs in ip_updates:
                self.update_host_ip(attrs['name'], attrs['fqdn'], attrs['newip'])
                rollback_ip_updates.append({'fqdn': attrs['fqdn'],
                                            'name': attrs['name'],
                                            'ip': attrs['oldip']})
            if hostname_update:
                self.update_host_name(hostname_update['ifname'],hostname_update['oldfqdn'],hostname_update['newfqdn'])

            for attrs in adds:
                self.add_host_details(attrs['fqdn'], attrs['ip'],
                                      attrs['name'], attrs['mac'],
                                      attrs['primary'], attrs['comments'])
                rollback_adds.append(attrs)

        except ProcessException, e:
            self.logger.info("Failed updating DSDB entry for {0:l}: "
                             "{1!s}".format(dbhw_ent, e))
            rollback_failures = []
            for attrs in rollback_adds:
                try:
                    self.delete_host_details(attrs['ip'])
                except Exception, err:
                    rollback_failures.append(str(err))
            if hostname_update:
                try:
                    self.update_host_name(hostname_update['ifname'],hostname_update['newfqdn'],hostname_update['oldfqdn'])
                except Exception, err:
                    rollback_failures.append(str(err))
            for attrs in rollback_ip_updates:
                try:
                    self.update_host_ip(**attrs)
                except Exception, err:
                    rollback_failures.append(str(err))
            for attrs in rollback_updates:
                try:
                    self.update_host_details(**attrs)
                except Exception, err:
                    rollback_failures.append(str(err))
            for attrs in rollback_deletes:
                try:
                    self.add_host_details(attrs['fqdn'], attrs['ip'],
                                          attrs['name'], attrs['mac'],
                                          attrs['primary'], attrs['comments'])
                except Exception, err:
                    rollback_failures.append(str(err))

            msg = "DSDB update failed: %s" % e
            if rollback_failures:
                msg += "\n\nRollback also failed, DSDB state is inconsistent:" + \
                        "\n".join(rollback_failures)
            raise AquilonError(msg)
        return

    def add_dns_domain(self, dns_domain, comments):
        if not comments:
            comments = ""
        try:
            out = run_command([self.dsdb, "add_dns_domain",
                               "-domain_name", dns_domain,
                               "-comments", comments], env=self.getenv())
        except ProcessException, e:
            if e.out and DNS_DOMAIN_EXISTS.search(e.out):
                self.logger.info("The DNS domain %s already exists in DSDB, "
                                 "continuing." % dns_domain)
                return
            raise

    def delete_dns_domain(self, dns_domain):
        try:
            out = run_command([self.dsdb, "delete_dns_domain",
                               "-domain_name", dns_domain], env=self.getenv())
        except ProcessException, e:
            if e.out and DNS_DOMAIN_NOT_FOUND.search(e.out):
                self.logger.info("The DNS domain %s does not exist in DSDB, "
                                 "proceeding with aqdb command." % dns_domain)
                return
            raise
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

        out = run_command([self.dsdb, "show_host",
                           "-host_name", fields["dsdb_lookup"]],
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

    def add_alias(self, alias, target, comments):
        if not comments:
            comments = ""
        run_command([self.dsdb, "add_host_alias", "-host_name", target,
                     "-alias_name", alias, "-comments", comments],
                    env=self.getenv())

    def del_alias(self, alias):
        run_command([self.dsdb, "delete_host_alias", "-alias_name", alias],
                    env=self.getenv())

    def update_alias(self, alias, target, comments):
        if not comments:
            comments = ""
        run_command([self.dsdb, "update_host_alias", "-alias", alias,
                     "-new_host", target, "-new_comments", comments],
                    env=self.getenv())


class NASAssign(object):

    def __init__(self, machine, disk, owner, rack=None, size=None):
        self.machine = str(machine)
        self.disk = str(disk)
        self.owner = str(owner)
        self.rack = str(rack)
        self.size = size
        self.config = Config()
        if self.config.getboolean('nasassign', 'use_dev_db'):
            self.devdb = 1
        self.laf_dict = {'_id':'%s_%s' % (self.disk, self.machine),
                         'owner':self.owner, 'rack':self.rack, 'size':self.size,
                         'devdb':self.devdb}
        self.bin = self.config.get('nasassign', 'bin')
        self.cmdline_args = self.config.get('nasassign', 'cmdline_args')
        self.args = [ self.bin ]
        if self.cmdline_args:
            self.args.extend(self.cmdline_args.split())

    def yaml(self):
        return yaml.dump(self.laf_dict, explicit_start=True,
                         default_flow_style=True, indent=2, tags=False)

    def create(self):
        if not self.rack or not self.size:
            raise ArgumentError("Must set rack and size attributes to "
                                "create nas assignments.")
        args = self.args[:]
        args.extend(['create', '-'])
        output = run_command(args, input=self.yaml())
        response_obj = yaml.load(output)
        if response_obj.get('sharename'):
            self.sharename = response_obj['sharename']
            return response_obj['sharename']
        else:
            #parse error output if possible, else just stringify it.
            error = str(response_obj.get('_error', {}).get('why', output))
            #check for parsable 'default handler' error from LAF
            try:
                default_handler_errors = response_obj['_error']['why']['default']
            except:
                default_handler_errors = []
            if error.startswith("Requested number of nas slots "
                                "are not available"):
                raise ArgumentError("No available NAS capacity in Resource Pool "
                                    "for rack %s. Please notify an "
                                    "administrator or add capacity." % self.rack)
            for dherr in default_handler_errors:
                if dherr.startswith("data@size"):
                    sizes = re.findall("\[([\d+, ]+)\]", dherr)
                    raise ArgumentError("Invalid size for autoshare disk. "
                                        "Supported sizes are: %s" % sizes )
            raise AquilonError("Received unexpected output from nasassign "
                               "/ resource pool: %s" % error)

    def delete(self):
        args = self.args[:]
        args.extend(['delete', '-'])
        output = run_command(args, input=self.yaml())
        response_obj = yaml.load(output)
        if response_obj:
            error = str(response_obj.get('_error', {}).get('why', output))
            raise AquilonError("Received unexpected output from nasassign "
                               "/ resource pool: %s" % error)
        else:
            self.sharename = None
            return True
