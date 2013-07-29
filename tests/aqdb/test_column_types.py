#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" Tests all the custom data types we create for aqd """

from utils import load_classpath, add, commit
load_classpath()

from sqlalchemy import MetaData, Table, Column, Integer, insert, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from nose.tools import raises

from aquilon.aqdb.column_types import IPV4, AqStr

dsn  = 'sqlite:///:memory:'
eng  = create_engine(dsn)

IP_TABLE = Table('foo', MetaData(dsn),
                 Column('id', Integer, primary_key=True),
                 Column('e', IPV4()))

Base = declarative_base()
Base.metadata.bind = eng
Session = sessionmaker()

s = Session()

class StringTbl(Base):
    __tablename__ = 'aqstr_test'
    id = Column(Integer, primary_key=True)
    name = Column(AqStr(16), nullable=False, unique=True)

    def __repr__(self):
        return self.__class__.__name__ + ' "' + str(self.name) + '"'

def setup():
    #TODO: ALL the setup ??? Or do they go into a suite level setup?
    IP_TABLE.create()
    StringTbl.__table__.create()
#No teardown for in memory tables =D

def test_valid_ipv4():
    """ tests simple insertion of valid ip addresses """

    IP_TABLE.insert().execute(e='192.168.1.1')
    IP_TABLE.insert().execute(e='144.14.47.54')

    result = list(IP_TABLE.select().execute())

    assert len(result) > 0, 'failed valid IPV4 insert'

@raises(TypeError)
def test_bad_input():
    """ test an invalid string as input """
    IP_TABLE.insert().execute(e='lalalala')

### AqStr Tests ###
def test_valid_aqstr():
    a = StringTbl(name='Hi there')
    add(s, a)
    commit(s)

    s.expunge_all()
    rec = s.query(StringTbl).first()
    print rec.name
    assert rec.name == 'hi there', 'String not lowercase in AqStr'

def test_whitespace_padding():
    a=StringTbl(name='  some eXTRa space     ')
    add(s, a)
    commit(s)

    p = StringTbl.__table__.select().execute().fetchall()[1]
    assert p['name'].startswith('s'), 'Whitespace not stripped in AqStr'
    print a


if __name__ == "__main__":
    import nose
    nose.runmodule()
