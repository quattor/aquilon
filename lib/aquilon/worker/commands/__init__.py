# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
import logging
from traceback import format_exc
from inspect import isclass

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
        except Exception, e:  # pragma: no cover
            log.msg("Error importing %s: %s" % (modulename, format_exc()))
            continue
        if not hasattr(mymodule, "BrokerCommand"):  # pragma: no cover
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
                mymodule.broker_command.module_logger = \
                        logging.getLogger(modulename)
                __all__.append(moduleshort)
                break
