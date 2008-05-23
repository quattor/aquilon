#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

import sys, os
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
        msg = "Standard out closed"
        if self.stderr_msgs:
            msg = msg + ": " + "".join(self.stderr_msgs)
        self.proto.connectionLost(error.ConnectionLost(msg))
        protocol.ProcessProtocol.outConnectionLost(self)

    def errConnectionLost(self):
        log.msg("Standard err closed")
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

