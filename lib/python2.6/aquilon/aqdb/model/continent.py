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
""" Continent is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location


class Continent(Location):
    """ Continent is a subtype of location """
    __tablename__ = 'continent'
    __mapper_args__ = {'polymorphic_identity': 'continent'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='continent_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

continent = Continent.__table__  # pylint: disable=C0103
continent.info['unique_fields'] = ['name']
