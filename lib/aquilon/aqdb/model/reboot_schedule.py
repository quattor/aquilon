# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016  Contributor
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

from sqlalchemy import String, Column, ForeignKey

from aquilon.aqdb.model import (Resource, Intervention)

_TN_RES = 'reboot_schedule'
_TN_IV = 'reboot_intervention'


class RebootSchedule(Resource):
    """ RebootSchedule resources """
    __tablename__ = _TN_RES

    resource_id = Column(ForeignKey(Resource.id, ondelete='CASCADE'),
                         primary_key=True)

    # str representation of time '00:00'
    time = Column(String(5), nullable=True)
    # str comma sep list of weeks 1-4
    week = Column(String(16), nullable=False)
    # str short day (long enough to accept a comma sep list, but for now we're
    # only accepting one).
    day = Column(String(32), nullable=False)

    __table_args__ = ({'info': {'unique_fields': ['name', 'holder']}},)
    __mapper_args__ = {'polymorphic_identity': 'reboot_schedule'}


class RebootIntervention(Intervention):
    """ RebootIntervention resources """
    __tablename__ = _TN_IV
    # Hack: Should probably just increase the length of the field to
    # support the string reboot_intervention.

    intervention_id = Column(ForeignKey(Intervention.resource_id,
                                        ondelete='CASCADE'), primary_key=True)

    __table_args__ = ({'info': {'unique_fields': ['name', 'holder']}},)
    __mapper_args__ = {'polymorphic_identity': 'reboot_iv'}
