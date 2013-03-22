#!/usr/bin/env python2.6
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
