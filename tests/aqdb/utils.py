#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" A collection of testing utilities for the AQDB package """
import os
import sys
import inspect

def load_classpath():
    """ Sets up the class path for aquilon """

    _DIR = os.path.dirname(os.path.realpath(__file__))
    _LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.6")
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
