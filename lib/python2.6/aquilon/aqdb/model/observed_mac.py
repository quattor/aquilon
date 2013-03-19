# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Observed Mac's are represent the occurance of seeing a mac address on
    the cam table of a given switch. They are created to allow for automated
    machine builds and ip assignment """

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Switch
from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.column_types import AqStr

_TN = 'observed_mac'


class ObservedMac(Base):
    """ reports the observance of a mac address on a switch port. """
    __tablename__ = _TN

    switch_id = Column(Integer, ForeignKey('switch.hardware_entity_id',
                                           ondelete='CASCADE',
                                           name='obs_mac_hw_fk'),
                       primary_key=True)

    port = Column(AqStr(32), primary_key=True)

    mac_address = Column(AqMac(17), nullable=False, primary_key=True)


    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    last_seen = Column('last_seen', DateTime,
                       default=datetime.now, nullable=False)

    switch = relation(Switch, backref=backref('observed_macs',
                                              cascade='delete',
                                              order_by=[port]))


observedmac = ObservedMac.__table__  # pylint: disable=C0103
observedmac.primary_key.name = '%s_pk' % _TN
