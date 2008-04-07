#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Handling of external processes for the broker happens here."""

import os
from tempfile import mkdtemp

from twisted.internet import utils, threads, defer
from twisted.python import log

from aquilon.exceptions_ import ProcessException, RollbackException

def _cb_cleanup_dir(arg, dir):
    """This callback is meant as a finally block to clean up the directory."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except exceptions.OSError, e:
                log.err(str(e))
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except exceptions.OSError, e:
                log.err(str(e))
    try:
        os.rmdir(dir)
    except exceptions.OSError, e:
        log.err(str(e))
    return arg

class ProcessBroker(object):

    # It might also be useful for this method to passthrough an argument,
    # instead of returning out.
    def cb_shell_command_finished(self, (out, err, code), command):
        log.msg("command `%s` finished with return code %d" % (command, code))
        log.msg("command `%s` stdout: %s" % (command, out))
        log.msg("command `%s` stderr: %s" % (command, err))
        if code != 0:
            raise ProcessException(command=command, out=out, err=err, code=code)
        return out

    # It might also be useful for this method to passthrough an argument,
    # instead of returning out.
    def cb_shell_command_error(self, (out, err, signalNum), command):
        log.msg("command `%s` exited with signal %d" % (command, signalNum))
        log.msg("command `%s` stdout: %s" % (command, out))
        log.msg("command `%s` stderr: %s" % (command, err))
        raise ProcessException(command=command, out=out, err=err,
                signalNum=signalNum)

    def run_shell_command(self, command):
        d = utils.getProcessOutputAndValue("/bin/sh", ["-c", command])
        return d.addCallbacks(self.cb_shell_command_finished,
                self.cb_shell_command_error,
                callbackArgs=[command], errbackArgs=[command])

    def sync(self, **kwargs):
        """Implements the heavy lifting of the aq sync command.
        
        Will raise ProcessException if one of the commands fails."""
        d = self.run_shell_command(("cd '%(domaindir)s'" +
                """ && env PATH="%(git_path)s:$PATH" git pull""") % kwargs)
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        d = d.addCallback(lambda _: self.run_shell_command(("cd '%(domaindir)s'"
            + """ && env PATH="%(git_path)s:$PATH" git update server info""")
            % kwargs))
        return d

    def wrap_failure_with_rollback(self, failure, **kwargs):
        # The idea here is to flag the ProcessException as something that
        # should trigger a rollback.  Maybe any exception should trigger
        # a rollback...
        error = failure.trap(ProcessException)
        raise RollbackException(cause=error, **kwargs)

    def write_file(self, filename, content):
        # FIXME: Wrap errors in a ProcessException?
        def _write_file():
            f = open(filename, 'w')
            f.write(content)
            f.close()

        # FIXME: Threading seems to create headaches for error handling...
        return threads.deferToThread(_write_file)
        #return defer.maybeDeferred(_write_file)

    def make_aquilon(self, (fqdn, buildid, template_string),
            basedir):
        """This expects to be called with the results of the dbaccess
        method of the same name."""
        # FIXME: This should probably be done off on a thread, and maybe
        # in a specific subdirectory...
        tempdir = mkdtemp()
        filename = os.path.join(tempdir, fqdn) + '.tpl'
        log.msg("writing the template to %s" % filename)
        d = self.write_file(filename, template_string)
        # FIXME: Pass these in from the broker...
        compiler = "/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc"
        # FIXME: Should be using the appropriate domain basedir.
        includes = [ basedir, "/ms/dev/elfms/ms-templates/1.0/src/distro" ]
        include_line = ""
        for i in includes:
            include_line = include_line + ' -I "' + i + '" '
        d = d.addCallback(lambda _: self.run_shell_command(compiler +
                include_line + ' -y ' + filename
                + ' >' + os.path.join(tempdir, fqdn) + '.xml'))
        # FIXME: Do we want to save off the built xml file anywhere
        # before the temp directory gets cleaned up?
        d = d.addBoth(_cb_cleanup_dir, tempdir)
        d = d.addErrback(self.wrap_failure_with_rollback, jobid=buildid)
        return d

#if __name__=='__main__':
