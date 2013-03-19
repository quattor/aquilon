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
""" ChassisSlot sets up a structure for tracking position within a chassis. """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Machine, Chassis

_TN = 'chassis_slot'


class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = _TN

    chassis_id = Column(Integer, ForeignKey('chassis.hardware_entity_id',
                                            name='%s_chassis_fk' % _TN,
                                            ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='%s_machine_fk' % _TN),
                        nullable=True)
    # TODO: need a unique key against this, but what if it takes 2 slots?
    # TODO: remove delete-orphan?
    chassis = relation(Chassis,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       order_by=[slot_number]))

    # No delete-orphan here, it's fine to leave the slot in place even if the
    # machine is removed
    machine = relation(Machine,
                       backref=backref('chassis_slot', cascade='all'))


chassis_slot = ChassisSlot.__table__  # pylint: disable=C0103
chassis_slot.primary_key.name = '%s_pk' % _TN
