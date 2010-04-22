# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
        except Exception, e:
            log.msg("Error importing %s: %s" % (modulename, format_exc()))
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
                mymodule.broker_command.module_logger = \
                        logging.getLogger(modulename)
                __all__.append(moduleshort)
                break
