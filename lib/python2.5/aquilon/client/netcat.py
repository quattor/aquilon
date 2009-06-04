#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Code to make connections with twisted through netcat."""


import os
import sys

from twisted.internet import reactor, protocol, address, error
from twisted.python import log


class NetCatConnector(protocol.ProcessProtocol):
    """
    I provide the glue to marry a BaseProtocol with a ProcessProtocol.

    This allows for "standard" protocols to run over stdin/stdout.
    """

    def __init__(self, proto, controller):
        self.proto = proto
        self.controller = controller
        self.stderr_msgs = []

    def connectionMade(self):
        log.msg("Subprocess started.")
        self.proto.makeConnection(self)

    # Transport
    disconnecting = False

    def write(self, data):
        self.transport.write(data)

    def writeSequence(self, data):
        self.transport.writeSequence(data)

    def loseConnection(self):
        self.transport.loseConnection()

    # XXX: Should call IPv4Address with a dotted quad and ensure that
    #      port is an int.
    def getPeer(self):
        return address.IPv4Address('TCP', self.host, self.port)

    # XXX: Should call IPv4Address with a dotted quad and ensure that
    #      port is an int.
    def getHost(self):
        return address.IPv4Address('TCP', self.host, self.port)

    def inConnectionLost(self):
        log.msg("Standard in closed")
        protocol.ProcessProtocol.inConnectionLost(self)

    def outConnectionLost(self):
        log.msg("Standard out closed")
        # For now, the child's standard out is "good enough"
        # that the connection is lost.
        self.transport.closeStdin()
        protocol.ProcessProtocol.outConnectionLost(self)

    def errConnectionLost(self):
        log.msg("Standard err closed")
        msg = "".join(self.stderr_msgs).strip()
        if msg:
            self.proto.connectionLost(error.ConnectionLost(msg))
        protocol.ProcessProtocol.errConnectionLost(self)

    def outReceived(self, data):
        log.msg("Received data from child")
        #print >>sys.stderr, str(data)
        #import pdb
        #pdb.set_trace()
        self.proto.dataReceived(data)

    def errReceived(self, data):
        log.msg("Received stderr from subprocess: " + str(data))
        self.stderr_msgs.append(str(data))

    def processEnded(self, status):
        log.msg("Process ended")
        self.proto.connectionLost(status)
        self.controller.childProcessTerminated(status)


class NetCatController(object):
    def __init__(self, proto, host, port):
        self.proto = proto
        self.host = host
        self.port = port

    def childProcessTerminated(self, status):
        log.msg(repr(status))
        #reactor.stop()

    # FIXME: Should probably try to reactor.resolve() the name here first
    # before calling nc.  Once resolved, NetCatConnector could
    # return correct IPv4Address values for getHost() and getPeer().
    def startProcess(self):
        executable = '/usr/bin/nc'
        env = os.environ
        self.connector = NetCatConnector(self.proto, self)
        
        args = (
            executable,
            self.host,
            str(self.port) )
        self.process = reactor.spawnProcess(self.connector, executable, args, env=env)


if __name__ == '__main__':
    from twisted.protocols.basic import LineReceiver
    host = "localhost"
    port = "6900"
    p = NetCatController(LineReceiver(), host, port)
    reactor.callWhenRunning(p.startProcess)
    reactor.run()


