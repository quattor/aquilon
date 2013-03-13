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
""" Desk is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location
from aquilon.aqdb.column_types.aqstr import AqStr


class Desk(Location):
    """ Desk is a subtype of location """
    __tablename__ = 'desk'
    __mapper_args__ = {'polymorphic_identity':'desk'}
    id = Column(Integer, ForeignKey('location.id',
                                    name='desk_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

desk = Desk.__table__
desk.primary_key.name='desk_pk'

table = desk


