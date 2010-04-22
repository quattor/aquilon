# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
from sqlalchemy.sql.expression import asc

from aquilon.aqdb.model import Base, Machine, Chassis

class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = 'chassis_slot'

    chassis_id = Column(Integer, ForeignKey('chassis.system_id',
                                            name='chassis_slot_chassis_fk',
                                            ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='chassis_slot_machine_fk'),
                        nullable=True)
    #TODO: need a unique key against this, but what if it takes 2 slots?

    chassis = relation(Chassis, uselist=False,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       order_by=[asc('slot_number')]),
                       passive_deletes=True)

    machine = relation(Machine, uselist=False,
                       backref=backref('chassis_slot',
                                       cascade='delete, delete-orphan'))

chassis_slot = ChassisSlot.__table__
chassis_slot.primary_key.name='chassis_slot_pk'

table = chassis_slot
