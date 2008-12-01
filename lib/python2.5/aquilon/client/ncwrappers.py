# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper for connections through netcat."""


from twisted.web import client
from twisted.python import log
from twisted.internet import reactor

from aquilon.client.netcat import NetCatController


def getPage(url, contextFactory=None, aquser=None, *args, **kwargs):
    """Download a web page as a string."""
    scheme, host, port, path = client._parse(url)
    factory = client.HTTPClientFactory(url, *args, **kwargs)
    p = NetCatController(factory.buildProtocol(None), host, port)
    reactor.callWhenRunning(p.startProcess)
    return factory.deferred

