# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Suggested versions of external libraries, and the defaults for the
    binaries shipped.
"""

import sys

import ms.version

ms.version.addpkg('lxml', '3.2.5')

if sys.platform == "sunos5":
    # ctypes is missing from the default Python build on Solaris, due to
    # http://bugs.python.org/issue2552. It is available as a separate package
    # though.
    ms.version.addpkg("ctypes", "1.0.2")

    # required to move the ctypes path  before the core paths
    sys.path.insert(0, sys.path.pop())
