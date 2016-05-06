#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
import logging
import argparse

import ms.version
ms.version.addpkg('twisted', '12.0.0')
ms.version.addpkg('zope.interface', '3.6.1')
ms.version.addpkg('setuptools', '0.6c11')
ms.version.addpkg('protobuf', '3.0.0b2')
ms.version.addpkg('six', '1.7.3')
ms.version.addpkg('python-daemon', '2.0.5')
ms.version.addpkg('lockfile', '0.9.1')

from twisted.internet.protocol import Factory
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet import reactor
from google.protobuf.json_format import MessageToJson

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

from aquilon.config import Config
from daemon import DaemonContext
from daemon.pidfile import TimeoutPIDLockFile

class EventProtocol(Int32StringReceiver):
    def __init__(self, storedir):
        self.storedir = storedir
        # Late import of protocol buffers after path correction
        import aqdnotifications_pb2
        self.skeleton = aqdnotifications_pb2.Notification

    def stringReceived(self, data):
        msg = self.skeleton()
        msg.ParseFromString(data)
        json_str = MessageToJson(msg)
        if self.storedir:
            path = os.path.join(self.storedir, '{}.json'.format(msg.uuid))
            with open(path, 'w') as fh:
                fh.write(json_str)
        else:
            sys.stdout.write(json_str)
            sys.stdout.write('\n')


class EventFactory(Factory):
    def __init__(self, storedir):
        self.storedir = storedir

    def buildProtocol(self, addr):
        return EventProtocol(self.storedir)


def run_reactor(sockname, storedir):
    reactor.listenUNIX(sockname, EventFactory(storedir))
    reactor.run()


def daemonize(pidfile, sockname, storedir):
    pidcmgr = TimeoutPIDLockFile(pidfile)
    with DaemonContext(pidfile=pidcmgr) as dc:
        run_reactor(sockname, storedir)


def main():
    parser = argparse.ArgumentParser(description="Send out broker notifications")
    parser.add_argument("-d", "--daemon", action='store_true',
                        help="Run as a daemon process")
    parser.add_argument("-s", "--store", action='store_true',
                        help="Write messages to a file")
    parser.add_argument("-c", "--config", dest="config",
                        help="location of the broker configuration file")
    opts = parser.parse_args()

    logger = logging.getLogger("read_events")

    # Load configuration
    config = Config(configfile=opts.config)

    # Load the specified version of the protcol buffers
    sys.path.append(config.get("protocols", "directory"))

    # Find and create the socket directory
    sockdir = config.get("broker", "sockdir")
    if not os.path.exists(sockdir):
        os.makedirs(sockdir)

    # Remove a stale socket
    sockname = os.path.join(sockdir, "events")
    if os.path.exists(sockname):
        logger.info("Removing old socket " + sockname)
        try:
            os.unlink(sockname)
        except OSError as err:
            logger.error("Failed to remove %s: %s", sockname, err)

    # Are we storing messages we recieve?
    storedir = None
    if opts.store:
        if config.has_section('unittest'):
            storedir = os.path.join(config.get('unittest', 'scratchdir'), 'events')
        else:
            storedir = os.path.join(config.get('quattordir'), 'scratch', 'events')
        if not os.path.exists(storedir):
            os.makedirs(storedir)

    # Decide if we want to daemionize
    if opts.daemon:
        rundir = config.get('broker', 'rundir')
        if not os.path.exists(rundir):
            os.makedirs(rundir)
        pidfile = os.path.join(rundir, 'read_events.pid')
        daemonize(pidfile, sockname, storedir)
    else:
        run_reactor(sockname, storedir)


if __name__ == '__main__':
    main()
