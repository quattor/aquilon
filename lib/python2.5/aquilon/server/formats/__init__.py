#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Initialize all the formatting handlers."""


import os
from traceback import format_exc

from twisted.python import log


__all__ = []

_thisdir = os.path.dirname(os.path.realpath(__file__))
for f in os.listdir(_thisdir):
    full = os.path.join(_thisdir, f)
    if os.path.isfile(full) and f.endswith('.py') and f != '__init__.py':
        moduleshort = f[:-3]
        modulename = __name__ + '.' + moduleshort
        try:
            mymodule = __import__(modulename, fromlist=["BrokerCommand"])
        except Exception, e:
            log.msg("Error importing %s: %s" % (modulename, format_exc()))
            continue


#if __name__=='__main__':
