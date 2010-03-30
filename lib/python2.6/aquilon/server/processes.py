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

from aquilon.exceptions_ import ProcessException, AquilonError, ArgumentError
from aquilon.config import Config

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
        if not envname.startswith("KRB"):
            continue
        shell_env[envname] = envvalue

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
    else:
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

def run_git_command(config, args, env=None, path=".",
                    logger=LOGGER, loglevel=logging.INFO):
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
        out = run_git_command(config, "describe", logger=logger,
                              path=config.get("broker", "srcdir"))
        config.set("broker", "version", out.strip())
    except ProcessException, e:
        logger.info("Could not run git describe to get version: %s" % e)
        config.set("broker", "version", "Unknown")


IP_NOT_DEFINED_RE = re.compile("Host with IP address "
                               "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
                               " is not defined")

class DSDBRunner(object):

    def __init__(self, logger=LOGGER):
        self.config = Config()
        self.logger = logger

    def getenv(self):
        if self.config.getboolean("broker", "dsdb_use_testdb"):
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def add_host(self, dbinterface):
        if not dbinterface.system.ip:
            raise ArgumentError("No ip address found for '%s' to add to dsdb." %
                                dbinterface.system.fqdn)
        return self.add_host_details(dbinterface.system.fqdn,
                                     dbinterface.system.ip,
                                     dbinterface.name, dbinterface.mac)

    def add_host_details(self, fqdn, ip, name, mac):
        # DSDB does not accept '/' as valid in an interface name.
        interface = str(name).replace('/', '_')
        command = [self.config.get("broker", "dsdb"),
                    "add", "host", "-host_name", fqdn,
                    "-ip_address", ip, "-status", "aq",
                    "-interface_name", interface]
        if mac:
            command.extend(["-ethernet_address", mac])
        out = run_command(command,env=self.getenv())
        return

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
#        for interface in dbhost.machine.interfaces:
#            if not interface.boot:
#                continue
#            self.delete_host_details(interface.ip)
#            return
#        raise ArgumentError("No boot interface found for host to delete from dsdb.")

    def update_host(self, dbinterface, oldinfo):
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
            self.add_host(dbinterface)
        except ProcessException, pe1:
            self.logger.info("Failed adding new information to dsdb, "
                             "attempting to restore old info.")
            try:
                self.add_host_details(dbinterface.system.fqdn, oldinfo["ip"],
                        oldinfo["name"], oldinfo["mac"])
            except ProcessException, pe2:
                # FIXME: Add details.
                raise AquilonError("DSDB is now in an inconsistent state.  Removing old information succeeded, but cannot add new information.")
            self.logger.info("Restored old info, re-raising the problem "
                             "with the add.")
            raise pe1
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
