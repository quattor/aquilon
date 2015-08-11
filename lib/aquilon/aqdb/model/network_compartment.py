# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
""" Contains tables and objects for authorization in Aquilon """
from datetime import datetime
import re

from sqlalchemy import Column, Integer, String, DateTime, Sequence
from sqlalchemy.orm import deferred, validates

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

from aquilon.exceptions_ import ArgumentError

_TN = 'network_compartment'


class NetworkCompartment(Base):
    """
    Network Compartment

    For networks compartmentalization is the establishment of boundaries
    between networks having different security constraints.  That is to
    say that a firewall exists between two networks in different network
    compartments.
    """
    __tablename__ = _TN
    _class_label = 'Network Compartment'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(32), nullable=False, unique=True)

    creation_date = deferred(Column(DateTime, nullable=False,
                                    default=datetime.now))

    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = ({'info': {'unique_fields': ['name']}},)

    _name_check = re.compile(r"^[a-z][a-z0-9_]+(\.[a-z0-9_]+)*$")

    @validates('name')
    def validate_name(self, key, value):
        if not self._name_check.match(value):
            raise ArgumentError("Illegal network compartment tag '%s'." %
                                value)
        return value
