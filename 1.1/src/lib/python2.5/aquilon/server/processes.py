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

from twisted.internet import utils
from twisted.python import log

from aquilon.exceptions_ import ProcessException

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

#if __name__=='__main__':
