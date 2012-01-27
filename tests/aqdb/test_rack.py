#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
""" Tests the validator functionality for the rack table """

from utils import load_classpath, add, commit
load_classpath()

import aquilon.aqdb.depends
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base, Location, Rack

from nose.tools import raises

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DSN = 'sqlite:///:memory:'
ENG = create_engine(DSN)
Base.metadata.bind = ENG

Session = sessionmaker(bind=ENG)
s = Session()
assert s, 'No session in test_rack'


def setup():
    print 'set up'
    for cls in Location, Rack:
        cls.__table__.create()


def testNormalInput():
    """ test valid rack characters """
    a = Rack(name='r1', fullname='r1', rack_row='FOO')
    add(s, a)
    commit(s)
    assert a.rack_row == 'foo', 'valid input lowercased'


@raises(ArgumentError)
def testWithBangCharacter():
    """ test invalid characters"""
    a = Rack(name='r2', fullname='r2', rack_column='bar!!!')
    add(s, a)
    commit(s)
    assert a.name


def testWithExtraSpaces():
    """ test strip and lower case"""
    a = Rack(name='r3', fullname='r3', rack_row='  BaZ  ')
    add(s, a)
    commit(s)
    assert a.rack_row == 'baz'


@raises(ArgumentError)
def testBadUpdate():
    """ test update coverage """
    a = s.query(Rack).first()
    a.rack_row = '%s!!!' % (a.rack_row)
    commit(s)
    assert a.rack_row == 'foo'


if __name__ == "__main__":
    import nose
    nose.runmodule()
