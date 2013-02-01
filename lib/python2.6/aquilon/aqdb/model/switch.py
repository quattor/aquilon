# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
""" Switches """
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import HardwareEntity
from aquilon.aqdb.column_types import Enum

SWITCH_TYPES = ('tor', 'bor', 'agg', 'misc')
_TN = 'switch'


class Switch(HardwareEntity):
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}

    hardware_entity_id = Column(Integer,
                                ForeignKey('hardware_entity.id',
                                           name='%s_hw_ent_fk' % _TN,
                                           ondelete='CASCADE'),
                                           primary_key=True)

    switch_type = Column(Enum(16, SWITCH_TYPES), nullable=False)

    last_poll = Column(DateTime, nullable=False, default=datetime.now)

    @classmethod
    def check_type(cls, type):
        if type is not None and type not in SWITCH_TYPES:
            raise ArgumentError("Unknown switch type '%s'." % type)


switch = Switch.__table__  # pylint: disable=C0103
switch.primary_key.name = 'switch_pk'
