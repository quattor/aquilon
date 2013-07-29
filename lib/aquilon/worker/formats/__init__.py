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
