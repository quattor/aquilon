# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Handling of external processes for the broker happens here.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""

import os
import re
import logging
from subprocess import Popen, PIPE
from threading import Thread

from mako.lookup import TemplateLookup

from aquilon.exceptions_ import (ProcessException, AquilonError, ArgumentError,
                                 InternalError)
from aquilon.config import Config, running_from_source
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
                               self.process.poll() is not None):
                break
            if data != '':
                if self.filterre and not self.filterre.search(data):
                    continue
                self.buffer.append(data)
                # This log output will appear in the server logs without
                # correct channel information.  We will re-log it separately
                # and with the correct info.
                self.logger.log(self.loglevel, data.rstrip())


def run_command(args, env=None, path="/", logger=LOGGER, loglevel=logging.INFO,
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
    logger.info("run_command: %s (CWD: %s)", simple_command,
                os.path.abspath(path))

    if input:
        proc_stdin = PIPE
        logger.info("command `%s` stdin: %s", simple_command, input)
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
        logger.info("command `%s` exited with return code %d", simple_command,
                    p.returncode)
    else:  # pragma: no cover
        logger.info("command `%s` exited with signal %d", simple_command,
                    -p.returncode)
    out = "".join(out_thread.buffer)
    if out:
        filter_msg = "filtered " if filterre else ""
        logger.info("command `%s` %sstdout: %s", simple_command,
                    filter_msg, out)
    err = "".join(err_thread.buffer)
    if err:
        logger.info("command `%s` stderr: %s", simple_command, err)

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

    for name in ["git_author_name", "git_author_email",
                 "git_committer_name", "git_committer_email"]:
        if not config.has_option("broker", name):
            continue
        value = config.get("broker", name)
        git_env[name.upper()] = value

    if isinstance(args, list):
        git_args = args[:]
        if git_args[0] != "git":
            git_args.insert(0, "git")
    else:
        git_args = ["git", args]

    return run_command(git_args, env=git_env, path=path,
                       logger=logger, loglevel=loglevel, filterre=filterre)


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
    kingdir = config.get("broker", "kingdir")
    domaindir = os.path.join(config.get("broker", "domainsdir"), dbdomain.name)
    git_env = {"PATH": "%s:%s" % (config.get("broker", "git_path"),
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


IP_NOT_DEFINED_RE = re.compile(r"Host with IP address "
                               r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
                               r" is not defined")

BUILDING_NOT_FOUND = re.compile(r"bldg [a-zA-Z0-9]{2} doesn't exists")

CAMPUS_NOT_FOUND = re.compile(r"campus [a-zA-Z0-9]{2} doesn't exist")

DNS_DOMAIN_NOT_FOUND = re.compile(r"DNS domain ([-\w\.\d]+) doesn't exists")

DNS_DOMAIN_EXISTS = re.compile(r"DNS domain [-\w\.\d]+ already defined")

# The regexp is taken from DSDB
INVALID_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]")


class DSDBRunner(object):

    def __init__(self, logger=LOGGER):
        config = Config()
        self.logger = logger
        self.dsdb = config.get("broker", "dsdb")
        self.dsdb_use_testdb = config.getboolean("broker", "dsdb_use_testdb")
        self.location_sync = config.getboolean("broker", "dsdb_location_sync")
        self.actions = []
        self.rollback_list = []

    def normalize_iface(self, iface):
        return INVALID_NAME_RE.sub("_", iface)

    def commit(self, verbose=False):
        for args, rollback, error_filter, ignore_msg in self.actions:
            cmd = [self.dsdb]
            cmd.extend(args)

            try:
                if verbose:
                    self.logger.client_info("DSDB: %s" %
                                            " ".join([str(a) for a in args]))
                run_command(cmd, env=self.getenv(), logger=self.logger)
            except ProcessException, err:
                if error_filter and err.out and error_filter.search(err.out):
                    self.logger.warn(ignore_msg)
                else:
                    raise

            if rollback:
                self.rollback_list.append(rollback)

    def rollback(self, verbose=False):
        self.rollback_list.reverse()
        rollback_failures = []
        for args in self.rollback_list:
            cmd = [self.dsdb]
            cmd.extend(args)
            try:
                self.logger.client_info("DSDB: %s" %
                                        " ".join([str(a) for a in args]))
                run_command(cmd, env=self.getenv(), logger=self.logger)
            except ProcessException, err:
                rollback_failures.append(str(err))

        did_something = bool(self.rollback_list)
        del self.rollback_list[:]

        if rollback_failures:
            raise AquilonError("DSDB rollback failed, DSDB state is "
                               "inconsistent: " + "\n".join(rollback_failures))
        elif did_something:
            self.logger.client_info("DSDB rollback completed.")

    def commit_or_rollback(self, error_msg=None, verbose=False):
        try:
            self.commit(verbose=verbose)
        except ProcessException, err:
            if not error_msg:
                error_msg = "DSDB update failed"
            self.logger.warn(str(err))
            self.rollback(verbose=verbose)
            raise ArgumentError(error_msg)

    def add_action(self, command_args, rollback_args, error_filter=None,
                   ignore_msg=False):
        """
        Register an action to execute and it's rollback counterpart.

        command_args: the DSDB command to execute
        rollback_args: the DSDB command to execute on rollback
        error_filter: regexp of error messages in the output of dsdb that
                      should be ignored
        ignore_msg: message to log if the error_filter matched
        """
        if error_filter and not ignore_msg:
            raise InternalError("Specifying an error filter needs the message "
                                "specified as well.")
        self.actions.append((command_args, rollback_args, error_filter,
                             ignore_msg))

    def getenv(self):
        if self.dsdb_use_testdb:
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def add_campus(self, campus, comments):
        if not self.location_sync:
            return

        command = ["add_campus_aq", "-campus_name", campus]
        if comments:
            command.extend(["-comments", comments])
        rollback = ["delete_campus_aq", "-campus", campus]
        self.add_action(command, rollback)

    def del_campus(self, campus):
        if not self.location_sync:
            return
        command = ["delete_campus_aq", "-campus", campus]
        rollback = ["add_campus_aq", "-campus_name", campus]
        self.add_action(command, rollback, CAMPUS_NOT_FOUND,
                        "DSDB does not have campus %s defined, proceeding.")

    def add_city(self, city, country, fullname):
        if not self.location_sync:
            return
        command = ["add_city_aq", "-city_symbol", city, "-country_symbol",
                   country, "-city_name", fullname]
        rollback = ["delete_city_aq", "-city", city]
        self.add_action(command, rollback)

    def update_city(self, city, campus, prev_campus):
        if not self.location_sync:
            return
        command = ["update_city_aq", "-city", city, "-campus", campus]
        # We can't revert to an empty campus
        if prev_campus:
            rollback = ["update_city_aq", "-city", city, "-campus", prev_campus]
        else:
            rollback = None
        self.add_action(command, rollback)

    def del_city(self, city, old_country, old_fullname):
        if not self.location_sync:
            return
        command = ["delete_city_aq", "-city", city]
        rollback = ["add_city_aq", "-city_symbol", city, "-country_symbol",
                    old_country, "-city_name", old_fullname]
        self.add_action(command, rollback)

    def add_campus_building(self, campus, building):
        if not self.location_sync:
            return
        command = ["add_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        rollback = ["delete_campus_building_aq", "-campus_name", campus,
                    "-building_name", building]
        self.add_action(command, rollback)

    def add_building(self, building, city, building_addr):
        if not self.location_sync:
            return
        command = ["add_building_aq", "-building_name", building, "-city", city,
                   "-building_addr", building_addr]
        rollback = ["delete_building_aq", "-building", building]
        self.add_action(command, rollback)

    def del_campus_building(self, campus, building):
        if not self.location_sync:
            return
        command = ["delete_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        rollback = ["add_campus_building_aq", "-campus_name", campus,
                    "-building_name", building]
        self.add_action(command, rollback)

    def del_building(self, building, old_city, old_addr):
        if not self.location_sync:
            return
        command = ["delete_building_aq", "-building", building]
        rollback = ["add_building_aq", "-building_name", building,
                    "-city", old_city, "-building_addr", old_addr]
        self.add_action(command, rollback, BUILDING_NOT_FOUND,
                        "DSDB does not have building %s defined, "
                        "proceeding." % building)

    def update_building(self, building, address, old_addr):
        if not self.location_sync:
            return
        command = ["update_building_aq", "-building_name", building,
                   "-building_addr", address]
        rollback = ["update_building_aq", "-building_name", building,
                    "-building_addr", old_addr]
        self.add_action(command, rollback)

    def add_host_details(self, fqdn, ip, iface=None, mac=None, primary=None,
                         comments=None, **kwargs):
        command = ["add_host", "-host_name", fqdn,
                   "-ip_address", ip, "-status", "aq"]
        if iface:
            command.extend(["-interface_name", self.normalize_iface(iface)])
        if mac:
            command.extend(["-ethernet_address", mac])
        if primary and str(primary) != str(fqdn):
            command.extend(["-primary_host_name", primary])
        if comments:
            command.extend(["-comments", comments])

        rollback = ["delete_host", "-ip_address", ip]
        self.add_action(command, rollback)

    def update_host_details(self, fqdn, iface=None, new_ip=None, new_mac=None,
                            new_comments=None, old_ip=None, old_mac=None,
                            old_comments=None, **kwargs):
        command = ["update_aqd_host", "-host_name", fqdn]
        if iface:
            iface = self.normalize_iface(iface)
            command.extend(["-interface_name", iface])

        rollback = command[:]

        if new_ip and new_ip != old_ip:
            command.extend(["-ip_address", new_ip])
            rollback.extend(["-ip_address", old_ip])
        if new_mac and new_mac != old_mac:
            command.extend(["-ethernet_address", new_mac])
            rollback.extend(["-ethernet_address", old_mac])
        if new_comments != old_comments:
            command.extend(["-comments", new_comments or ""])
            rollback.extend(["-comments", old_comments or ""])

        self.add_action(command, rollback)

    def update_host_iface_name(self, old_fqdn, new_fqdn,
                               old_iface, new_iface, **kwargs):
        old_iface = self.normalize_iface(old_iface)
        new_iface = self.normalize_iface(new_iface)
        command = ["update_aqd_host", "-host_name", old_fqdn]
        rollback = ["update_aqd_host", "-host_name", new_fqdn]

        if old_fqdn != new_fqdn:
            command.extend(["-new_host_name", new_fqdn])
            rollback.extend(["-new_host_name", old_fqdn])
        if old_iface and old_iface != new_iface:
            command.extend(["-interface_name", old_iface,
                            "-new_interface_name", new_iface])
            rollback.extend(["-interface_name", new_iface,
                             "-new_interface_name", old_iface])

        self.add_action(command, rollback)

    def delete_host_details(self, fqdn, ip, iface=None, mac=None, primary=None,
                            comments=None, **kwargs):
        command = ["delete_host", "-ip_address", ip]
        rollback = ["add_host", "-host_name", fqdn,
                    "-ip_address", ip, "-status", "aq"]
        if iface:
            rollback.extend(["-interface_name", self.normalize_iface(iface)])
        if mac:
            rollback.extend(["-ethernet_address", mac])
        if primary and str(primary) != str(fqdn):
            rollback.extend(["-primary_host_name", primary])
        if comments:
            rollback.extend(["-comments", comments])

        self.add_action(command, rollback, IP_NOT_DEFINED_RE,
                        "DSDB did not have a host with this IP address, "
                        "proceeding.")

    @classmethod
    def snapshot_hw(cls, dbhw_ent):
        """
        Make a snapshot of the interface parameters.

        update_host() will use this snapshot to decide what has changed and
        what DSDB commands have to be executed.

        Comment handling is a bit complicated, because we have more ways to
        store comments in Aquilon than in DSDB. The rules are:

        - If the interface has a comment, use that.

        - Otherwise take the comment from the hardware entity.

          Exception: management interfaces
        """

        real_primary = dbhw_ent.fqdn
        hwdata = {"by-ip": {},
                  "by-fqdn": {},
                  "primary": real_primary}

        # We need a stable index for generating virtual interface names for
        # DSDB. Sort the Zebra IPs and use the list index for this purpose.
        # There is an exception though: while renumbering and thus
        # deleting/re-adding the virtual interfaces is generally fine, we do not
        # want to remove the primary IP address. So make sure the primary IP is
        # always the first one.
        zebra_ips = []
        for addr in dbhw_ent.all_addresses():
            if addr.network.is_internal and \
               addr.service_address and \
               addr.service_address.holder.holder_type == 'host' and \
               addr.ip not in zebra_ips:
                    zebra_ips.append(addr.ip)
        zebra_ips.sort()
        if dbhw_ent.primary_ip and dbhw_ent.primary_ip in zebra_ips:
            zebra_ips.remove(dbhw_ent.primary_ip)
            zebra_ips.insert(0, dbhw_ent.primary_ip)

        # For each of the addresses held by this hardware_entity we need to
        # create an entry in DSDB.  The following loop makes a snapshot of
        # expected state of the information in DSDB.
        for addr in dbhw_ent.all_addresses():
            # Do not propergate to DSDB if the network is not internal, or
            # there are no FQDN's associated with this address.
            if not addr.network.is_internal:
                continue
            if not addr.fqdns:
                continue

            # In AQDB there may be multiple domain names associated with
            # an address, in DSDB there can only be one.  Thus we pick
            # the first address to propergate.
            fqdn = str(addr.fqdns[0])

            # By default we take the comments from the hardware_entity,
            # if an interface comment exists then this will be taken
            # in preference.  Management interfaces are added as stand-alone
            # entries, therefore we do not take the hardware_entity comment
            # but allow the following code to take it from the interface.
            if addr.interface.interface_type != 'management':
                comments = dbhw_ent.comments
            else:
                comments = None

            # Determine the interface name and comments used by this address.
            if addr.ip in zebra_ips:
                # Zebra: in AQDB the address is assigned to multiple existing
                # interfaces. In DSDB however, we need just a single virtual
                # interface
                iface = "le%d" % zebra_ips.index(addr.ip)
            elif addr.service_address:
                # Skip cluster-bound service addresses
                continue
            else:
                iface = addr.logical_name
                if addr.interface.comments and not \
                   addr.interface.comments.startswith("Created automatically"):
                    comments = addr.interface.comments

            # Determine if we need to specify a primary name to DSDB.  By
            # doing so we are associating this record with another.
            # Note, the existance of a primary hostname effects the order
            # that entriers are processed in update_host()
            if addr.interface.interface_type == "management":
                # Do not use -primary_host_name for the management address
                # as we do not wish to associate them with the host currently
                # on the machine (which may change).
                primary = None
            elif addr.service_address:
                # Do not use -primary_host_name for service addresses, because
                # srvloc does not like that
                primary = None
            elif fqdn == real_primary:
                # Do not set the 'primary' key for the real primary name.
                primary = None
            else:
                # In all other cases associate the record with the primary name.
                primary = real_primary

            # Exclude the MAC address for aliases
            if addr.label:
                mac = None
            else:
                mac = addr.interface.mac

            ifdata = {'iface': iface,
                      'ip': addr.ip,
                      'mac': mac,
                      'fqdn': fqdn,
                      'primary': primary,
                      'comments': comments}

            hwdata["by-ip"][ifdata["ip"]] = ifdata
            hwdata["by-fqdn"][ifdata["fqdn"]] = ifdata

        return hwdata

    def update_host(self, dbhw_ent, old_hwdata):
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
        if dbhw_ent:
            new_hwdata = self.snapshot_hw(dbhw_ent)
        else:
            new_hwdata = {"by-ip": {},
                          "by-fqdn": {},
                          "primary": None}

        if not old_hwdata:
            old_hwdata = {"by-ip": {},
                          "by-fqdn": {},
                          "primary": None}

        deletes = []
        adds = []
        # Host/interface names cannot be updated simultaneously with IP/MAC
        # addresses or comments
        addr_updates = []
        name_updates = []

        # Run through all of the entries in the old snapshot and attempt
        # to match them to their corrisponding new entry.
        for fqdn, old_ifdata in old_hwdata["by-fqdn"].items():
            # Locate the new information about this address by either
            # its FQDN or IP address.
            if fqdn in new_hwdata["by-fqdn"]:
                new_ifdata = new_hwdata["by-fqdn"][fqdn]
            elif old_ifdata["ip"] in new_hwdata["by-ip"]:
                new_ifdata = new_hwdata["by-ip"][old_ifdata["ip"]]
            else:
                new_ifdata = None

            # If either the old or the new entry is bound to a primary name but
            # the other is not, then we have to delete & re-add it.  Note this
            # will be re-added in the following loop as we did not delete the
            # entry from new_hwdata.
            if new_ifdata and bool(old_ifdata["primary"]) != bool(new_ifdata["primary"]):
                new_ifdata = None

            # If there is no new data then record a delete (note above).
            if not new_ifdata:
                deletes.append(old_ifdata)
                continue

            # Create a dict with entries in old_ifdata prefiexd with 'old_'
            # and entries in new_ifdata prefixed with 'new_'
            kwargs = dict((p + k, v)
                          for (p, d) in [('old_', old_ifdata),
                                         ('new_', new_ifdata)]
                          for k, v in d.iteritems())

            if old_ifdata['ip'] != new_ifdata['ip'] or \
               old_ifdata['mac'] != new_ifdata['mac'] or \
               old_ifdata['comments'] != new_ifdata['comments']:
                addr_updates.append(kwargs)

            if old_ifdata['fqdn'] != new_ifdata['fqdn'] or \
               old_ifdata['iface'] != new_ifdata['iface']:
                name_updates.append(kwargs)

            # Delete the entries from new_hwdata.  We have recorded an
            # update.  The contents of new_hwdata is used in the following
            # loop to record additions.
            del new_hwdata["by-fqdn"][new_ifdata["fqdn"]]
            del new_hwdata["by-ip"][new_ifdata["ip"]]

        # For all of the recoreds remaining in new_hwdata (see above)
        # record an addtion opperation.
        adds = new_hwdata["by-fqdn"].values()

        # Add the primary address first, and delete it last. The primary address
        # is identified by having an empty ['primary'] key (this is true for the
        # management address as well, but that does not matter).
        sort_by_primary = lambda x, y: cmp(x['primary'] or "", y['primary'] or "")
        adds.sort(sort_by_primary)
        deletes.sort(sort_by_primary, reverse=True)

        for attrs in deletes:
            self.delete_host_details(**attrs)

        for kwargs in addr_updates:
            # The old FQDN and interface name are the fixed point
            self.update_host_details(fqdn=kwargs['old_fqdn'],
                                     iface=kwargs['old_iface'],
                                     **kwargs)

        for kwargs in name_updates:
            self.update_host_iface_name(**kwargs)

        for attrs in adds:
            self.add_host_details(**attrs)

    def add_dns_domain(self, dns_domain, comments):
        if not comments:
            # DSDB requires the comments field, even if it is empty
            comments = ""
        command = ["add_dns_domain", "-domain_name", dns_domain,
                   "-comments", comments]
        rollback = ["delete_dns_domain", "-domain_name", dns_domain]
        self.add_action(command, rollback, DNS_DOMAIN_EXISTS,
                        "The DNS domain %s already exists in DSDB, "
                        "proceeding." % dns_domain)

    def delete_dns_domain(self, dns_domain, old_comments):
        command = ["delete_dns_domain", "-domain_name", dns_domain]
        rollback = ["add_dns_domain", "-domain_name", dns_domain,
                    "-comments", old_comments]
        self.add_action(command, rollback, DNS_DOMAIN_NOT_FOUND,
                        "The DNS domain %s does not exist in DSDB, "
                        "proceeding." % dns_domain)

    rack_row_re = re.compile(r'^\s*Row:\s*\b([-\w]+)\b$', re.M)
    rack_col_re = re.compile(r'^\s*Column:\s*\b([-\w]+)\b$', re.M)

    def show_rack(self, rackname):

        out = run_command([self.dsdb, "show_rack",
                           "-rack_name", rackname],
                          env=self.getenv())
        rack_row = self.rack_row_re.search(out)
        rack_col = self.rack_col_re.search(out)
        fields = {}
        fields["rack_row"] = rack_row and rack_row.group(1) or None
        fields["rack_col"] = rack_col and rack_col.group(1) or None

        if not fields["rack_row"] or not fields["rack_col"]:
            raise ValueError("Rack %s is missing row and/or col data")

        return fields

    primary_re = re.compile(r'^\s*Primary Name:\s*\b([-\w]+)\b$', re.M)
    node_re = re.compile(r'^\s*Node:\s*\b([-\w]+)\b$', re.M)
    dns_re = re.compile(r'^\s*DNS Domain:\s*\b([-\w\.]+)\b$', re.M)
    state_re = re.compile(r'^\s*State:\s*\b(\d+)\b$', re.M)

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
        command = ["add_host_alias", "-host_name", target,
                   "-alias_name", alias]
        if comments:
            command.extend(["-comments", comments])
        rollback = ["delete_host_alias", "-alias_name", alias]
        self.add_action(command, rollback)

    def del_alias(self, alias, old_target, old_comments):
        command = ["delete_host_alias", "-alias_name", alias]
        rollback = ["add_host_alias", "-host_name", old_target,
                    "-alias_name", alias]
        if old_comments:
            rollback.extend(["-comments", old_comments])
        self.add_action(command, rollback)

    def update_alias(self, alias, target, comments, old_target, old_comments):
        command = ["update_host_alias", "-alias", alias,
                   "-new_host", target]
        rollback = ["update_host_alias", "-alias", alias,
                    "-new_host", old_target]
        if comments != old_comments:
            command.extend(["-new_comments", comments or ""])
            rollback.extend(["-new_comments", old_comments or ""])
        self.add_action(command, rollback)


def build_mako_lookup(config, kind, **kwargs):
    # This duplicates the logic from lookup_file_path(), but we don't want to
    # move the mako dependency to aquilon.config
    srcdir = config.get("broker", "srcdir")
    srcpath = os.path.join(srcdir, "etc", "mako", kind)

    directories = []
    if running_from_source():
        # If we're running from the source, then ignore any installed files
        directories.append(srcpath)
    else:
        directories.append(os.path.join("/etc", "aquilon", "mako", kind))
        directories.append(os.path.join("/usr", "share", "aquilon", "mako", kind))
        if os.path.exists(srcpath):
            directories.append(srcpath)

    return TemplateLookup(directories=directories, **kwargs)
