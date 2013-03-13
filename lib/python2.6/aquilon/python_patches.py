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
"""Patches for stock python functionality."""


def load_uuid_quickly():
    """
    Do evil stuff to reduce initial import time of the uuid module.

    This is because it relies on ctypes.util.find_library, which does a
    bunch of work to figure out that the 'uuid' library is available as
    'libuuid.so'.  This module provides a helper to monkey-patch around
    that.

    Monkey-patch the ctype library finding code to be fast.  Load uuid
    (which uses this code), and then restore.  Note that this is not
    thread-safe.
    """
    import ctypes.util

    def find_library(name):
        return 'lib' + name + '.so'
    old_find_library = ctypes.util.find_library
    ctypes.util.find_library = find_library
    import uuid
    ctypes.util.find_library = old_find_library
    return uuid
