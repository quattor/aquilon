#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

import sys
import os
import socket
import logging
from logging.handlers import WatchedFileHandler
from threading import Thread, Condition
import signal
import errno

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib"))

import aquilon.aqdb.depends

import ms.version
ms.version.addpkg('argparse', '1.2.1')

import argparse

from aquilon.config import Config
from aquilon.exceptions_ import AquilonError

do_exit = False
worker_thread = None
worker_notify = None


def update_index_and_notify(config, logger, db):
    from aquilon.notify.index import build_index

    session = db.Session()

    try:
        build_index(config, session, logger)
    except AquilonError, err:
        logger.error(err)

    db.Session.remove()


class UpdaterThread(Thread):

    def __init__(self, config, logger, db, cond):
        self.config = config
        self.logger = logger
        self.db = db
        self.cond = cond
        self.update_queued = False
        super(UpdaterThread, self).__init__()

    def run(self):
        global do_exit

        while True:
            self.cond.acquire()
            if not self.update_queued:
                self.cond.wait(10.0)

            if do_exit:
                break
            if not self.update_queued:
                continue

            self.update_queued = False
            self.cond.release()

            self.logger.debug("Worker woken up")
            update_index_and_notify(self.config, self.logger, self.db)

            self.cond.acquire()

        self.cond.release()
        self.logger.info("Worker thread finished")


def run_loop(config, logger, db):
    global do_exit, worker_thread, worker_notify

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sockname = os.path.join(config.get("broker", "sockdir"), "notifysock")
    if os.path.exists(sockname):
        logger.info("Removing old socket " + sockname)
        try:
            os.unlink(sockname)
        except OSError, err:
            logger.error("Failed to remove %s: %s" % (sockname, err))
    listener.bind(sockname)
    listener.listen(5)
    logger.info("Listening on " + sockname)

    worker_notify = Condition()

    worker_thread = UpdaterThread(config, logger, db, worker_notify)
    worker_thread.start()

    while not do_exit:
        try:
            sd, addr = listener.accept()
        except IOError, err:
            if err.errno == errno.EINTR:
                continue
            raise

        logger.debug("Connection received")

        command = None
        try:
            command = sd.recv(128)
        except IOError:
            pass
        sd.close()

        command = command.strip()
        logger.debug("Command: '%s'" % command)

        if command == "update":
            # Wake up the worker thread
            worker_notify.acquire()
            worker_thread.update_queued = True
            worker_notify.notify()
            worker_notify.release()

            logger.debug("Update queued")

    logger.info("Shutting down")
    listener.close()
    os.unlink(sockname)
    worker_thread.join()


def exit_handler(signum, frame):
    global do_exit
    do_exit = True

    logger = logging.getLogger("aq_notifyd")
    logger.info("Received signal %d" % signum)

    # Wake up the worker thread
    worker_notify.acquire()
    worker_notify.notify()
    worker_notify.release()


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

    # These modules must be imported after the configuration has been
    # initialized
    from aquilon.aqdb.db_factory import DbFactory

    db = DbFactory()

    if opts.debug:
        level = logging.DEBUG
        logging.basicConfig(level=level, stream=sys.stderr,
                            format='%(asctime)s [%(levelname)s] %(message)s')
    else:
        level = logging.INFO
        logfile = os.path.join(config.get("broker", "logdir"), "aq_notifyd.log")

        handler = WatchedFileHandler(logfile)
        handler.setLevel(level)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)

        rootlog = logging.getLogger()
        rootlog.addHandler(handler)
        rootlog.setLevel(level)

    # Apply configured log settings
    for logname, level in config.items("logging"):
        if level not in logging._levelNames:
            continue
        logging.getLogger(logname).setLevel(logging._levelNames[level])

    logger = logging.getLogger("aq_notifyd")

    if opts.one_shot:
        update_index_and_notify(config, logger, db)
    else:
        signal.signal(signal.SIGTERM, exit_handler)
        signal.signal(signal.SIGINT, exit_handler)

        run_loop(config, logger, db)


if __name__ == '__main__':
    main()
