# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

from string import capitalize
from datetime import datetime

from sqlalchemy import (Integer, DateTime, Sequence, String, Column, Boolean,
                        UniqueConstraint, ForeignKey)

from aquilon.aqdb.model import (Resource, Intervention)
from aquilon.aqdb.column_types.aqstr import AqStr

_TN_RES = 'reboot_schedule'

class RebootSchedule(Resource):
    """ RebootSchedule resources """
    __tablename__ = _TN_RES
    __mapper_args__ = {'polymorphic_identity': 'reboot_schedule'}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='rs_resource_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    # str representation of time '00:00'
    time = Column(String(5), nullable=True)
    # str comma sep list of weeks 1-5
    week = Column(String(16), nullable=False)
    # str short day (long enough to accept a comma sep list, but for now we're
    # only accepting one).
    day = Column(String(32), nullable=False)

reboot_schedule = RebootSchedule.__table__
reboot_schedule.primary_key.name = '%s_pk' % (_TN_RES)
reboot_schedule.info['unique_fields'] = ['name', 'holder']

_TN_IV = 'reboot_intervention'

class RebootIntervention(Intervention):
    """ RebootIntervention resources """
    __tablename__ = _TN_IV
    # Hack: Should probably just increase the length of the field to
    # support the string reboot_intervention.
    __mapper_args__ = {'polymorphic_identity': 'reboot_iv'}

    id = Column(Integer, ForeignKey('intervention.id',
                                    name='ri_resource_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

reboot_intervention = RebootIntervention.__table__
reboot_intervention.primary_key.name = '%s_pk' % (_TN_IV)
reboot_intervention.info['unique_fields'] = ['name', 'holder']

