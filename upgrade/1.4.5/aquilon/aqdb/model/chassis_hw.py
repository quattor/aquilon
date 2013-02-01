# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
""" The hardware portion of a chassis. The chassis we use today are:
    HP: C class and P class, though p class servers have no central management
    IBM: BCE and BCH (blade center e and blade center h). There may be some
    blade center e's in VA but they are like rackmounts as well"""

from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import HardwareEntity

class ChassisHw(HardwareEntity):
    __tablename__ = 'chassis_hw'
    __mapper_args__ = {'polymorphic_identity':'chassis_hw'}

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name='chassis_hw_fk',
                                           ondelete='CASCADE'),
                                           primary_key=True)

    @property
    def hardware_name(self):
        if self.chassis_hw:
            return ",".join(chassis.fqdn for chassis in self.chassis_hw)
        return self._hardware_name

chassis_hw = ChassisHw.__table__
chassis_hw.primary_key.name='chassis_hw_pk'

table = chassis_hw


