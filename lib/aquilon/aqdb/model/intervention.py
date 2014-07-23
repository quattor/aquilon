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

from datetime import datetime

from sqlalchemy import Integer, DateTime, String, Column, ForeignKey

from aquilon.aqdb.model import Resource

_TN = 'intervention'


class Intervention(Resource):
    """ time-based resource """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'intervention'}

    id = Column(Integer, ForeignKey(Resource.id,
                                    name='iv_resource_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    start_date = Column(DateTime, default=datetime.now, nullable=False)
    expiry_date = Column(DateTime, default=datetime.now, nullable=False)
    justification = Column(String(255), nullable=True)

    # what users/groups to allow access during the intervention
    # this as a string will go away and become association proxies
    # once we have users/groups in the system.
    users = Column(String(255), nullable=True)
    groups = Column(String(255), nullable=True)

    # actions to disable/enable (e.g. scheduled-reboot)
    disabled = Column(String(255), nullable=True)
    enabled = Column(String(255), nullable=True)

intervention = Intervention.__table__
intervention.info['unique_fields'] = ['name', 'holder']
