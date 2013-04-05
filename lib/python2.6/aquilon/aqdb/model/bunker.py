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
""" Bunker is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location

_TN = 'bunker'


class Bunker(Location):
    """ Bunker is a subtype of location """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}

    id = Column(Integer, ForeignKey('location.id',
                                    name='%s_loc_fk' % _TN,
                                    ondelete='CASCADE'),
                primary_key=True)


bunker = Bunker.__table__  # pylint: disable=C0103
bunker.primary_key.name = '%s_pk' % _TN
bunker.info['unique_fields'] = ['name']
