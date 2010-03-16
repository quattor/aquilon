#!/usr/bin/env python2.6

# Twisted, the Framework of Your Internet
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# Copyright (c) 2008,2009  Contributor
# See LICENSE for details.

# This is an (almost) completely new version of the script from
# the original twisted distributed.
# It was hacked to understand the MS layout.
# It was then enhanced (marked with comments below) to handle 8.1.0
# and again for 8.2.0.

import sys, os
sys.path.append( os.path.join(
                    os.path.dirname( os.path.realpath(sys.argv[0]) ),
                    "..", "lib", "python2.6" ) )

# avoid the warning on deprecated md5 module. will remove when
# a later version of twisted handles this
import warnings
warnings.simplefilter("ignore", DeprecationWarning)


import aquilon.server.depends
import aquilon.aqdb.depends

from twisted.scripts import twistd
from twisted.python import log, logfile

# This bit is taken from the twisted.application.app... we
# really want logging to start up before the app does.  This may need
# to be revisited on future twisted upgrades.  It did change going from
# 8.1.0 -> 8.2.0.  The below is based on 8.2.0.  The difference is that
# self.logger.start() is exploded to remove the requirement that the
# application exists and the application created afterwards.
def updated_application_run(self):
    """
    Run the application.
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

# Install the updated method.  Again, may break on upgrades and relies
# on the internals of twisted.scripts.twistd.
twistd._SomeApplicationRunner.run = updated_application_run

# Back to the original 2.5.0-based code.
twistd.run()
