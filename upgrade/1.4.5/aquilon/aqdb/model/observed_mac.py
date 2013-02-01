# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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

from sqlalchemy import Table, Column, Integer, DateTime, Sequence, ForeignKey
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.expression import asc

from aquilon.aqdb.model import Base, Network, TorSwitch
from aquilon.aqdb.column_types.aqmac import AqMac


class ObservedMac(Base):
    """ reports the observance of a mac address on a switch port. """
    __tablename__ = 'observed_mac'

    #TODO: code level constraint on machine_type == tor_switch
    switch_id = Column(Integer, ForeignKey('tor_switch.id',
                                              ondelete='CASCADE',
                                              name='obs_mac_hw_fk'),
                                             primary_key=True)

    port_number = Column(Integer, primary_key=True)

    mac_address = Column(AqMac(17), nullable=False, primary_key=True)

    slot = Column(Integer, nullable=True, default=1, primary_key=True)

    creation_date = deferred(Column('creation_date', DateTime,
                            default=datetime.now, nullable=False))

    last_seen = deferred(Column('last_seen', DateTime,
                            default=datetime.now, nullable=False))

    switch = relation(TorSwitch, backref=backref('observed_macs',
                                                 cascade='delete',
                                                 order_by=[asc('slot'),
                                                           asc('port_number')]))

    #TODO: selectable relation to interface/machine/system?

observed_mac = ObservedMac.__table__
observed_mac.primary_key.name='observed_mac_pk'

table = observed_mac


