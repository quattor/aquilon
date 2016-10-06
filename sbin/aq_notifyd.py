#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
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

import argparse
import sys
import os
import logging
from logging.handlers import WatchedFileHandler
from threading import Thread, Condition

try:
    import ms.version
except ImportError:
    pass
else:
    ms.version.addpkg('twisted', '12.0.0')
    ms.version.addpkg('zope.interface', '3.6.1')

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import aquilon.aqdb.depends  # pylint: disable=W0611

from aquilon.config import Config

worker_thread = None
worker_notify = Condition()


class NotifyProtocol(LineReceiver):
    delimiter = "\n"

    def lineReceived(self, line):
        logger = logging.getLogger("aq_notifyd")

        if line == "update":
            # Wake up the worker thread
            worker_notify.acquire()
            worker_thread.update_queued = True
            worker_notify.notify()
            worker_notify.release()

            logger.debug("Update queued")
        else:
            logger.warn("Unknown command: %s", line)


class NotifyFactory(Factory):
    protocol = NotifyProtocol


def update_index_and_notify(config, logger, db):
    from aquilon.notify.index import build_index

    session = db.Session()

    try:
        build_index(config, session, logger)
    except Exception as err:
        logger.error(err)
    finally:
        db.Session.remove()


class UpdaterThread(Thread):

    def __init__(self, config, logger, db):
        self.config = config
        self.logger = logger
        self.db = db
        self.update_queued = False
        self.do_exit = False
        super(UpdaterThread, self).__init__()

    def run(self):
        self.logger.info("Worker thread starting")

        while True:
            worker_notify.acquire()
            if not self.update_queued:
                worker_notify.wait(10.0)

            if self.do_exit:
                break
            if not self.update_queued:
                continue

            self.update_queued = False
            worker_notify.release()

            self.logger.debug("Worker woken up")
            update_index_and_notify(self.config, self.logger, self.db)

        worker_notify.release()
        self.logger.info("Worker thread finished")


def stop_worker():
    # Tell the worker thread to stop, and wait until it does
    worker_notify.acquire()
    worker_thread.do_exit = True
    worker_notify.notify()
    worker_notify.release()
    worker_thread.join()


def start_worker(config, logger, db):
    global worker_thread

    worker_thread = UpdaterThread(config, logger, db)
    worker_thread.start()


def run_loop(config, logger, db):
    sockname = os.path.join(config.get("broker", "sockdir"), "notifysock")
    if os.path.exists(sockname):
        logger.info("Removing old socket " + sockname)
        try:
            os.unlink(sockname)
        except OSError as err:
            logger.error("Failed to remove %s: %s", sockname, err)

    reactor.listenUNIX(sockname, NotifyFactory())
    reactor.addSystemEventTrigger("before", "startup", start_worker, config,
                                  logger, db)
    reactor.addSystemEventTrigger("after", "shutdown", stop_worker)
    reactor.run()

    logger.info("Shutting down")


def main():
    parser = argparse.ArgumentParser(description="Send out broker notifications")
    parser.add_argument("-c", "--config", dest="config",
                        help="location of the broker configuration file")
    parser.add_argument("--one_shot", action="store_true",
                        help="do just a single run and then exit")
    parser.add_argument("--debug", action="store_true",
                        help="turn on debug logs on stderr")

    opts = parser.parse_args()

    config = Config(configfile=opts.config)

    if config.has_option("broker", "umask"):
        os.umask(int(config.get("broker", "umask"), 8))

    if opts.debug:
        level = logging.DEBUG
        logging.basicConfig(level=level, stream=sys.stderr,
                            format='%(asctime)s [%(levelname)s] %(message)s')
    else:
        level = logging.INFO

        logdir = config.get("broker", "logdir")
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        logfile = os.path.join(logdir, "aq_notifyd.log")

        handler = WatchedFileHandler(logfile)
        handler.setLevel(level)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)

        rootlog = logging.getLogger()
        rootlog.addHandler(handler)
        rootlog.setLevel(level)

    # Apply configured log settings
    for logname, level in config.items("logging"):
        try:
            # TODO: Drop the translation from str to int when moving the min.
            # Python version to 2.7
            levelno = logging._levelNames[level]
            logging.getLogger(logname).setLevel(levelno)
        except (ValueError, KeyError):
            pass

    logger = logging.getLogger("aq_notifyd")

    # These modules must be imported after the configuration has been
    # initialized
    from aquilon.aqdb.db_factory import DbFactory

    db = DbFactory()

    if opts.one_shot:
        update_index_and_notify(config, logger, db)
    else:
        run_loop(config, logger, db)


if __name__ == '__main__':
    main()
