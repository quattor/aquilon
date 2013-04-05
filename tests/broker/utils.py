#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
""" Miscelaneous helper libraries for testing """


def import_depends():
    """ Set up the sys.path for loading library dependencies """
    import os
    import sys

    _DIR = os.path.dirname(os.path.realpath(__file__))
    _LIBDIR = os.path.join(_DIR, "..", "..", "lib")
    _TESTDIR = os.path.join(_DIR, "..")

    if _LIBDIR not in sys.path:
        sys.path.insert(0, _LIBDIR)

    if _TESTDIR not in sys.path:
        sys.path.insert(1, _TESTDIR)

    import depends
