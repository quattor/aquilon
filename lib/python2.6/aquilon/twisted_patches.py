# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
import errno

from twisted.python import log, syslog, logfile
from twisted.internet import reactor, error
from twisted.runner.procmon import ProcessMonitor


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
            proc.signalProcess('KILL')
        except error.ProcessExitedAlready:
            pass
        except OSError, e:
            # Ignore "No such process" errors.
            if e.errno != errno.ESRCH:
                raise

    def stopProcess(self, name):
        if name not in self.processes:
            log.msg("No record of %s to stop, ignoring." % name)
            raise KeyError("Unrecognized process name: %s" % name)
        proto = self.protocols.get(name, None)
        if not proto:
            return
        proc = proto.transport
        log.msg("Sending SIGTERM to %s [%s]" % (name, proc.pid))
        try:
            proc.signalProcess('TERM')
        except error.ProcessExitedAlready:
            log.msg("Process %s [%s] marked as exited already" %
                    (name, proc.pid))
        except OSError, e:
            if e.errno == errno.ESRCH:
                log.msg("Process %s [%s] pid does not exist" %
                        (name, proc.pid))
            else:
                raise
        else:
            # Hard-wire some actions for the final phase of shutdown,
            # assuming this method is scheduled to run 'before' 'shutdown'.
            reactor.addSystemEventTrigger('after', 'shutdown',
                                          self.killProcess, name, proc)

    # Replace connectionLost with a more conservative method during shutdown...
    stoppedConnectionLost = lambda self, name: log.msg('%s finished.' % name)

    def stopService(self):
        self.connectionLost = self.stoppedConnectionLost
        # Can't use super here as ProcessMonitor is an old-style object.
        return ProcessMonitor.stopService(self)


class BridgeLogHandler(logging.Handler):
    """Allow python logging messages to be funneled into the twisted log."""
    def emit(self, record):
        log.msg(record.getMessage())


def set_log_file(logFile, setStdout=True, start=True):
    """Set up twisted log files in a standard way.

    This borrows functionality from the twisted.application.app
    AppLogger.start() method, which in turn uses the
    twisted.scripts._twistd_unix.UnixAppLogger._getLogObserver method.

    That method returns a FileLog that is hard-coded to set a log
    rotation of 1 MB.  While we're here anyway, overriding that as well
    to remove the rotation size.  We rotate logs with an external
    logrotate command that sends SIGUSR1 to tell the broker to reopen
    the log file.

    """
    log_file = logfile.LogFile.fromFullPath(logFile, rotateLength=0)
    observer = log.FileLogObserver(log_file).emit
    try:
        import signal
    except ImportError:
        pass
    else:
        # Override if signal is set to None or SIG_DFL (0)
        if not signal.getsignal(signal.SIGUSR1):
            def restartLog(signal, frame):
                log_file.flush()
                try:
                    log_file.close()
                except:
                    pass
                log_file._openFile()
            signal.signal(signal.SIGUSR1, restartLog)
    if start:
        log.startLoggingWithObserver(observer, setStdout=setStdout)
    return observer

def updated_application_run(self):
    """Patch for twisted.application.app.ApplicationRunner.run().

    We really want logging to start up before the app does.  This has
    needed to change in every upgrade from 8.1.0 -> 8.2.0 -> 10.2.0.
    The difference for 8.2.0 is that self.logger.start() is exploded to
    remove the requirement that the application exists and the
    application created afterwards.  In 10.2.0 the logger.start()
    implementation changed.  The logic structure has been modified to
    enable set_log_file as a separate method.

    The exploded start() uses twisted.scripts._twistd_unix.UnixAppLogger's
    _getLogObserver method as a base.

    """
    self.preApplication()

    if self.logger._syslog:
        self.logger._observer = syslog.SyslogObserver(self._syslogPrefix).emit
    elif self.logger._logfilename == '-':
        if not self.logger._nodaemon:
            sys.exit('Daemons cannot log to stdout, exiting!')
        self.logger._observer = log.FileLogObserver(sys.stdout).emit
    elif self.logger._nodaemon and not self.logger._logfilename:
        self.logger._observer = log.FileLogObserver(sys.stdout).emit
    else:
        if not self.logger._logfilename:
            self.logger._logfilename = 'twistd.log'
        self.logger._observer = set_log_file(self.logger._logfilename,
                                             start=False)
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
