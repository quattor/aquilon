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
from tempfile import mkdtemp, mkstemp
from base64 import b64decode

from twisted.internet import utils, threads, defer
from twisted.python import log

from aquilon.exceptions_ import ProcessException, RollbackException, \
        DetailedProcessException, ArgumentError


def _cb_cleanup_dir(arg, dir):
    """This callback is meant as a finally block to clean up the directory."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except OSError, e:
                log.err(str(e))
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError, e:
                log.err(str(e))
    try:
        os.rmdir(dir)
    except OSError, e:
        log.err(str(e))
    return arg

def _cb_cleanup_file(arg, file):
    """This callback is meant as a finally block to clean up a file."""
    try:
        os.unlink(file)
    except OSError, e:
        log.err(str(e))
    return arg


class ProcessBroker(object):

    # It might also be useful for this method to passthrough an argument,
    # instead of returning out.
    def cb_shell_command_finished(self, (out, err, code), command):
        log.msg("command `%s` finished with return code %d" % (command, code))
        if out:
            log.msg("command `%s` stdout: %s" % (command, out))
        if err:
            log.msg("command `%s` stderr: %s" % (command, err))
        if code != 0:
            raise ProcessException(command=command, out=out, err=err, code=code)
        return out

    # It might also be useful for this method to passthrough an argument,
    # instead of returning out.
    def cb_shell_command_error(self, (out, err, signalNum), command):
        log.msg("command `%s` exited with signal %d" % (command, signalNum))
        if out:
            log.msg("command `%s` stdout: %s" % (command, out))
        if err:
            log.msg("command `%s` stderr: %s" % (command, err))
        raise ProcessException(command=command, out=out, err=err,
                signalNum=signalNum)

    def run_shell_command(self, result, command, env={}, path="."):
        # Forcibly string-ifying the command in the long run might not be such
        # a great idea, but this makes dealing with unicode simpler...
        command = str(command)
        d = utils.getProcessOutputAndValue("/bin/sh", ["-c", command],
                env, path)
        return d.addCallbacks(self.cb_shell_command_finished,
                self.cb_shell_command_error,
                callbackArgs=[command], errbackArgs=[command])

    def _create_tempdir(self, result, build_info):
        build_info["tempdir"] = mkdtemp()
        return result

    def create_tempdir(self, result, build_info):
        return threads.deferToThread(self._create_tempdir, result, build_info)

    def _cleanup_tempdir(self, result, build_info):
        tempdir = build_info.pop("tempdir", None)
        if tempdir:
            _cb_cleanup_dir(True, tempdir)
        return result

    def cleanup_tempdir(self, result, build_info):
        return threads.deferToThread(self._cleanup_tempdir, result, build_info)

    def sync(self, result, domain, git_path, templatesdir, **kwargs):
        """Implements the heavy lifting of the aq sync command.
        
        Will raise ProcessException if one of the commands fails."""

        domaindir = templatesdir + "/" + domain
        d = self.run_shell_command(True,
                """env PATH="%s:$PATH" git pull""" % git_path,
                path=domaindir)
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        d = d.addCallback(self.run_shell_command,
            """env PATH="%s:$PATH" git-update-server-info"""
            % git_path, path=domaindir)
        return d

    def wrap_failure_with_rollback(self, failure, **kwargs):
        # The idea here is to flag the ProcessException as something that
        # should trigger a rollback.  Maybe any exception should trigger
        # a rollback...
        error = failure.trap(ProcessException)
        raise RollbackException(cause=failure.value, **kwargs)

    def write_file(self, content, filename):
        # FIXME: Wrap errors in a ProcessException?
        def _write_file():
            f = open(filename, 'w')
            f.write(content)
            f.close()

        return threads.deferToThread(_write_file)

    def eb_pan_compile(self, failure, infile, outfile):
        failure.trap(ProcessException)
        input = ""
        if os.path.exists(infile):
            input = file(infile).read()
        output = failure.value.out
        if not output and os.path.exists(outfile):
            output = file(outfile).read()
        raise DetailedProcessException(failure.value, input, output)

    def compile_host(self, result, build_info, templatesdir, plenarydir,
            profilesdir, depsdir, hostsdir):
        """This expects build_info to have a dbhost and a tempdir with a
        template to try compiling.  On success, those files will be saved
        into the appropriate broker directories."""
        tempdir = build_info["tempdir"]
        dbhost = build_info["dbhost"]
        fqdn = dbhost.fqdn
        filename = os.path.join(tempdir, fqdn) + '.tpl'
        # FIXME: Pass these in from the broker...
        # 1.0 stores the compiler per-domain...
        compiler = "/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc"
        domain = dbhost.domain.name
        # FIXME: Should be based on the archetype of the host.
        domaindir = os.path.join(templatesdir, domain)
        aquilondir = os.path.join(domaindir, "aquilon")
        includes = [ aquilondir, domaindir, plenarydir,
                "/ms/dev/elfms/ms-templates/1.0/src/distro" ]
        include_line = " ".join(['-I "%s"' % include for include in includes])
        outfile = os.path.join(tempdir, fqdn + '.xml')
        outdep = outfile + '.dep'  # Yes, this ends with .xml.dep
        d = self.run_shell_command(True,
                'env PATH="/ms/dist/msjava/PROJ/sunjdk/1.6.0_04/bin:$PATH" '
                + compiler + ' ' + include_line + ' -y ' + filename,
                path=tempdir)
        # On error, the tempfile contents are captured into the
        # exception (since it will be cleaned out higher up).
        d = d.addErrback(self.eb_pan_compile, filename, outfile)
        # On success, the files get saved off.
        d = d.addCallback(self.run_shell_command, 'cp "%s" "%s"'
                % (outfile, profilesdir))
        d = d.addCallback(self.run_shell_command, 'cp "%s" "%s"'
                % (outdep, depsdir))
        d = d.addCallback(self.run_shell_command, 'cp "%s" "%s"'
                % (filename, hostsdir))
        # FIXME
        d = d.addErrback(self.wrap_failure_with_rollback,
                jobid=build_info["buildid"])
        return d

    def add_domain(self, result, domain, git_path, templatesdir, kingdir,
            **kwargs):
        """Domain has been added to the database.

        Now create the git repository.

        """
        domaindir = os.path.join(templatesdir, domain)
        # FIXME: If this command fails, the user should be notified.
        # FIXME: If this command fails, should the domain entry be
        # removed from the database?
        d = self.run_shell_command(True,
                """env PATH="%s:$PATH" git clone "%s" "%s" """
                % (git_path, kingdir, domaindir))
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        d = d.addCallback(self.run_shell_command,
            """env PATH="%s:$PATH" git-update-server-info"""
            % git_path, path=domaindir)
        # FIXME: 1.0 contains an initdomain() that would run here.
        # Most of it looks to now be irrelevant (part of the previous
        # ant build system)... none of it is included here (yet).
        return d

    def del_domain(self, result, domain, templatesdir, **kwargs):
        """Domain has been removed from the database (results in result).

        Now remove the directories.

        """
        domaindir = os.path.join(templatesdir, domain)
        d = threads.deferToThread(_cb_cleanup_dir, True, domaindir)
        # FIXME: The server also removes /var/quattor/build/cfg/domains/<domain>
        return d

    #def decode_and_write(self, filename, encoded):
        #decoded = b64decode(encoded)
        #return self.write_file(filename, decoded)

    def put(self, result, domain, bundle, basedir, templatesdir, git_path,
            **kwargs):
        # FIXME: Check that it exists.
        domaindir = templatesdir + "/" + domain
        # FIXME: How long can mkstemp() block?
        # FIXME: Maybe create the temp file under basedir somewhere.
        (handle, filename) = mkstemp()
        d = threads.deferToThread(b64decode, bundle)
        d = d.addCallback(self.write_file, filename)
        d = d.addCallback(self.run_shell_command,
            """env PATH="%s:$PATH" git bundle verify "%s" """
            % (git_path, filename), path=domaindir)
        d = d.addCallback(self.run_shell_command,
            """env PATH="%s:$PATH" git pull "%s" HEAD"""
            % (git_path, filename), path=domaindir)
        d = d.addCallback(self.run_shell_command,
            """env PATH="%s:$PATH" git-update-server-info"""
            % git_path, path=domaindir)
        d = d.addBoth(_cb_cleanup_file, filename)
        return d

    def deploy(self, result, fromdomain, todomain, basedir, templatesdir,
            kingdir, git_path, **kwargs):
        # FIXME: Check that it exists.
        fromdomaindir = templatesdir + "/" + fromdomain
        d = self.run_shell_command(True,
                """env PATH="%s:$PATH" git pull "%s" """
                % (git_path, fromdomaindir), path=kingdir)
        return d
    
    def pxeswitch(self, result, hostname, **kwargs):
        command = '/ms/dist/elfms/PROJ/aii/1.3.10-1/sbin/aii-installfe'
        args = []
        if kwargs.get('boot'):
            args.append('--boot')
        elif kwargs.get('install'):
            args.append('--install')
        else:
            raise ArgumentError("Missing required boot or install parameter.")
        # We may want to use result here, as it (should be) a gauranteed fqdn.
        args.append(hostname)
        args.append('2>&1')
        d = self.run_shell_command(True, command + ' ' + ' '.join(args))
        return d

    def eb_detailed_command(self, failure):
        failure.trap(ProcessException)
        raise DetailedProcessException(failure.value)

    # Hack to deal with IPs already in dsdb.  In theory, we *want* dsdb to
    # tell us when there are conflicts, but right now it isn't helping.
    def eb_ignore_already_defined(self, failure):
        failure.trap(ProcessException)
        if failure.value.out and failure.value.out.find("already defined") >= 0:
            log.msg("DSDB check failed, continuing anyway!")
            return True
        return failure

    # Expects to be run after dbaccess.verify_add_host.
    def add_host(self, (short, dbdns_domain, dbmachine), dsdb, **kwargs):
        """add_host only adds the primary interface (marked boot) to dsdb."""
        env = {"DSDB_USE_TESTDB": "true"}
        for interface in dbmachine.interfaces:
            if not interface.boot:
                continue
            d = self.run_shell_command(True,
                """%s add host -host_name "%s" -dns_domain "%s" -ip_address "%s" -status aq -interface_name "%s" -ethernet_address "%s" """
                % (dsdb, short, dbdns_domain.name, interface.ip,
                interface.name, interface.mac),
                env=env)
            # FIXME: This should not be used...
            d = d.addErrback(self.eb_ignore_already_defined)
            d = d.addErrback(self.eb_detailed_command)
            return d
        raise ArgumentError("No boot interface found for host to remove from dsdb.")
    
    # Expects to be run after dbaccess.verify_del_host.
    def del_host(self, result, dsdb, **kwargs):
        """del_host only removes the primary interface (boot) from dsdb."""

        dbmachine = result
        env = {"DSDB_USE_TESTDB": "true"}
        for interface in dbmachine.interfaces:
            if not interface.boot:
                continue
            d = self.run_shell_command(True,
                """%s delete host -ip_address "%s" """
                % (dsdb, interface.ip),
                env=env)
            d = d.addErrback(self.eb_detailed_command)
            return d
        raise ArgumentError("No boot interface found for host to add to dsdb.")

#if __name__=='__main__':
