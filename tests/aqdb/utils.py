#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
""" A collection of testing utilities for the AQDB package """
import os
import sys
import inspect

def load_classpath():
    """ Sets up the class path for aquilon """

    _DIR = os.path.dirname(os.path.realpath(__file__))
    _LIBDIR = os.path.join(_DIR, "..", "..", "lib")
    _TESTDIR = os.path.join(_DIR, "..")

    if _LIBDIR not in sys.path:
        sys.path.insert(0, _LIBDIR)

    if _TESTDIR not in sys.path:
        sys.path.insert(1, _TESTDIR)

    import depends
    import aquilon.aqdb.depends

def commit(sess):
    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

def add(sess, obj):
    try:
        sess.add(obj)
    except Exception, e:
        sess.rollback()
        raise e

def create(sess, obj):
    add(sess, obj)
    commit(sess)

def func_name():
    """ return the calling file and function name for useful assert messages """
    frame = inspect.stack()[1]
    return '%s.%s()' % (os.path.basename(frame[1]).rstrip('.py'), frame[3])
