#!/usr/bin/env python2.6
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
