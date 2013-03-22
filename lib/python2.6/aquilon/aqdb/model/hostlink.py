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

from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import validates

from aquilon.aqdb.model import Resource

_TN = 'hostlink'


class Hostlink(Resource):
    """ Hostlink resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'hostlink'}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='hostlink_resource_fk',
                                    ondelete='CASCADE'),
                                    primary_key=True)

    target = Column(String(255), nullable=False)
    owner_user = Column(String(32), default='root', nullable=False)
    owner_group = Column(String(32), nullable=True)

    @validates(owner_user, owner_group)
    def validate_owner(self, key, value):
        if ':' in value:
            raise ValueError("%s cannot contain the ':' character" % key)
        return value


hostlink = Hostlink.__table__
hostlink.primary_key.name = '%s_pk' % (_TN)
hostlink.info['unique_fields'] = ['name', 'holder']
