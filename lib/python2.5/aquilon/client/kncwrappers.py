# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
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


