# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016,2017  Contributor
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

from sqlalchemy import String, Integer, Column, ForeignKey, CheckConstraint
from sqlalchemy.sql import and_
from sqlalchemy.orm import validates

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Resource

_TN = 'hostlink'


class Hostlink(Resource):
    """ Hostlink resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'hostlink'}

    resource_id = Column(ForeignKey(Resource.id, ondelete='CASCADE'),
                         primary_key=True)

    target = Column(String(255), nullable=False)
    owner_user = Column(String(32), default='root', nullable=False)
    owner_group = Column(String(32), nullable=True)
    # "mode" is a reserved keyword in oracle, so use target_mode in the DB. 
    target_mode = Column(Integer, nullable=True)

    __table_args__ = (CheckConstraint(and_(target_mode > 0, target_mode <= 1023)),
                      {'info': {'unique_fields': ['name', 'holder']}},)


    @validates('target_mode')
    def validate_mode(self, key, value):
        if value is None:
            return None
        try:
            value = int(value, 8)
            if not (value > 0 and value <= 0o1777):
                raise ArgumentError("mode is out of range (0-1777 octal)")
            return value
        except ValueError:
            raise ArgumentError("mode does not convert to base 8 integer")

    @validates('owner_user', 'owner_group')
    def validate_owner(self, key, value):
        if value is not None:
            if ':' in value:
                raise ArgumentError("%s cannot contain the ':' character" % key)
        return value
