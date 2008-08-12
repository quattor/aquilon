#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Initialize each broker command and make it easy to load by installing
   an instance of the command as broker_command in the module.

   This ends up importing everything... any script in this directory
   will end up being triggered any time any module in this directory is
   loaded - side effects and all.

   Once loaded, this iterates through each module, finds the subclass of
   BrokerCommand and installs it as broker_command.  The module name is
   then added to __all__.

   """

import os
import sys
from inspect import isclass

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
            print >>sys.stderr, "Error importing %s: %s" % (modulename, e)
            continue
        if not hasattr(mymodule, "BrokerCommand"):
            continue
        # This is just convenient... don't have to import the 'real'
        # BrokerCommand, since any file we care about will have already
        # had to import it.
        BrokerCommand = mymodule.BrokerCommand
        for item in [getattr(mymodule, i) for i in dir(mymodule)]:
            if not isclass(item):
                continue
            if item.__module__ != mymodule.__name__:
                # Prevents us from accidently picking up base classes and
                # other imports.
                continue
            if issubclass(item, BrokerCommand):
                mymodule.broker_command = item()
                __all__.append(moduleshort)
                break


#if __name__=='__main__':
