# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Module for consolidating enhancements to stock twisted routines.

Note that many of the twisted objects are not new-style classes and
thus the code here cannot use super().

"""

import sys
import logging
from signal import SIGTERM, SIGKILL

from twisted.internet import reactor, process
from twisted.runner.procmon import ProcessMonitor
from twisted.python import log, logfile


class GracefulProcessMonitor(ProcessMonitor):
    """Updates ProcessMonitor for some real world use cases.

    The original stopProcess does not take into account that (in at
    least twisted 8.2.0 and on) the callLater method to send SIGKILL
    will never be called since stopProcess is invoked as a shutdown
    hook.

    Taking the opportunity to add some logging.

    Note that this class does not derive from object so it cannot
    use super().

    """
    def killProcess(self, name, proc):
        if not proc.pid:
            return
        try:
            log.msg("Sending SIGKILL to %s [%s]" % (name, proc.pid))
            proc.signalProcess(SIGKILL)
        except process.ProcessExitedAlready:
            pass

    def stopProcess(self, name):
        if not self.protocols.has_key(name):
            log.msg("No record of %s to stop, ignoring." % name)
            return
        proc = self.protocols[name].transport
        del self.protocols[name]
        try:
            log.msg("Sending SIGTERM to %s [%s]" % (name, proc.pid))
            proc.signalProcess(SIGTERM)
        except process.ProcessExitedAlready:
            log.msg("Process %s [%s] marked as exited already" % (name, proc.pid))
        else:
            # Hard-wire some actions for the final phase of shutdown,
            # assuming this method is scheduled to run 'before' 'shutdown'.
            reactor.addSystemEventTrigger('after', 'shutdown',
                                          self.killProcess, name, proc)


class BridgeLogHandler(logging.Handler):
    """Allow python logging messages to be funneled into the twisted log."""
    def emit(self, record):
        log.msg(record.getMessage())

def updated_application_run(self):
    """Patch for twisted.application.app.ApplicationRunner.run().

    We really want logging to start up before the app does.  This has
    needed to change in every upgrade.
    The difference for 8.2.0 is that self.logger.start() is exploded to
    remove the requirement that the application exists and the
    application created afterwards.

    """
    self.preApplication()

    # Instead of calling AppLogger.start() via self.logger.start(),
    # which requires the application to have been created, just do what
    # start() would do.
    # The first thing start() does is set its _observer to the return
    # value of _getLogObserver() which returns a FileLog that is hard-
    # coded to set a log rotation of 1 MB.  While we're here anyway,
    # overriding that as well to remove the rotation size.  We rotate
    # logs with an external logrotate command that sends SIGUSR1 to
    # tell the broker to reopen the log file.
    if self.logger._logfilename == '-' or not self.logger._logfilename:
        logFile = sys.stdout
    else:
        logFile = logfile.LogFile.fromFullPath(self.logger._logfilename,
                                               rotateLength=0)
        try:
            import signal
        except ImportError:
            pass
        else:
            # Override if signal is set to None or SIG_DFL (0)
            if not signal.getsignal(signal.SIGUSR1):
                def restartLog(signal, frame):
                    logFile.flush()
                    try:
                        logFile.close()
                    except:
                        pass
                    logFile._openFile()
                signal.signal(signal.SIGUSR1, restartLog)
    self.logger._observer = log.FileLogObserver(logFile).emit
    log.startLoggingWithObserver(self.logger._observer)
    self.logger._initialLog()

    self.application = self.createOrGetApplication()
    self.postApplication()
    self.logger.stop()

def integrate_logging(config):
    """Use a BridgeLogHandler to tie python's logging to twisted.python.log."""
    rootlog = logging.getLogger()
    rootlog.addHandler(BridgeLogHandler())
    rootlog.setLevel(logging.NOTSET)
    for logname in config.options("logging"):
        logvalue = config.get("logging", logname)
        # Complain if a config value is out of whack...
        if logvalue not in logging._levelNames:
            # ...but ignore it if it is a default (accidently
            # polluting the section).
            if not config.defaults().has_key(logname):
                log.msg("For config [logging]/%s, "
                        "%s not a valid log level." % (logname, logvalue))
            continue
        logging.getLogger(logname).setLevel(logging._levelNames[logvalue])

# Fix a deprecation warning in twisted 8.2.0 strports._funcs["unix"].
# The mode should not be passed.
def _parseUNIX(factory, address, mode='666', backlog=50, lockfile=True):
    return ((address, factory), {'backlog': int(backlog),
                                 'wantPID': bool(int(lockfile))})
