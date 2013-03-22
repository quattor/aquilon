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
""" Rack is a subclass of Location """

from sqlalchemy import Column, Integer, Numeric, ForeignKey

from aquilon.aqdb.model import Location
from aquilon.aqdb.column_types import AqStr

class Rack(Location):
    """ Rack is a subtype of location """
    __tablename__ = 'rack'
    __mapper_args__ = {'polymorphic_identity':'rack'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='rack_loc_fk',
                                    ondelete='CASCADE'), primary_key=True)

    #TODO: POSTHASTE: constrain to alphabetic in row, and make both non-nullable
    rack_row    = Column(AqStr(4), nullable=True)
    rack_column = Column(Integer, nullable=True)

rack = Rack.__table__
rack.primary_key.name = 'rack_pk'
table = rack

def populate(sess, *args, **kw):

    if len(sess.query(Rack).all()) < 1:
        from building import Building

        bldg = {}

        try:
            np = sess.query(Building).filter_by(name='np').one()
        except Exception, e:
            print e
            sys.exit(9)

        rack_name='np3'
        a = Rack(name = rack_name, fullname='Rack %s'%(rack_name),
                     parent = np, comments = 'AutoPopulated')
        sess.add(a)
        try:
            sess.commit()
        except Exception, e:
            print e



