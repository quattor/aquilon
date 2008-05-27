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

from twisted.web import client
from twisted.python import log
from netcat import NetCatController
from twisted.internet import reactor

def getPage(url, contextFactory=None, *args, **kwargs):
    """Download a web page as a string."""
    scheme, host, port, path = client._parse(url)
    factory = client.HTTPClientFactory(url, *args, **kwargs)
    p = NetCatController(factory.buildProtocol(None), host, port)
    reactor.callWhenRunning(p.startProcess)
    return factory.deferred

