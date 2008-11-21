# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper for knc connections."""


import os

from twisted.web import client
from twisted.python import log
from twisted.internet import reactor

from aquilon.client.netcat import NetCatConnector, NetCatController


class KNCController(NetCatController):
    def __init__(self, proto, host, port, service):
        NetCatController.__init__(self, proto, host, port)
        self.service = service

    # No need to override this ATM.
    #def childProcessTerminated(self, status):
    #    print status

    # FIXME: Should probably try to reactor.resolve() the name here first
    # before calling nc.  Once resolved, NetCatConnector could
    # return correct IPv4Address values for getHost() and getPeer()
    def startProcess(self):
        #executable = '/ms/dev/kerberos/knc/1.4/install/exec/bin/knc'
        executable = "/ms/dist/kerberos/PROJ/knc/prod/bin/knc"
        env = os.environ
        self.connector = NetCatConnector(self.proto, self)
        address = self.service + "@" + self.host         

        args = (
            executable,
            address,
            str(self.port) )
        #print "About to call: %s" % " ".join(args)
        self.process = reactor.spawnProcess(self.connector, executable, args, env=env)

def getPage(url, contextFactory=None, aquser="cdb", *args, **kwargs):
    """Download a web page as a string."""
    scheme, host, port, path = client._parse(url)
    factory = client.HTTPClientFactory(url, *args, **kwargs)
    p = KNCController(factory.buildProtocol(None), host, port, aquser)
    reactor.callWhenRunning(p.startProcess)
    return factory.deferred


