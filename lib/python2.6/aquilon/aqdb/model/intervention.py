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

from datetime import datetime

from sqlalchemy import (Integer, DateTime, Sequence, String, Column,
                        UniqueConstraint, ForeignKey)

from aquilon.aqdb.model import Resource
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'intervention'


class Intervention(Resource):
    """ time-based resource """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'intervention'}

    id = Column(Integer, ForeignKey('resource.id',
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
intervention.primary_key.name = '%s_pk' % (_TN)
intervention.info['unique_fields'] = ['name', 'holder']
