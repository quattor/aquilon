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
""" Polymorphic representation of disks which may be local or san """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Machine, ServiceInstance
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.config import Config

disk_types = ['local', 'san', 'virtual_disk']
controller_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash',
                    'fibrechannel']

_TN = 'disk'


class Disk(Base):
    """
        Base Class for polymorphic representation of disk or disk-like resources
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    disk_type = Column(Enum(64, disk_types), nullable=False)
    capacity = Column(Integer, nullable=False)
    device_name = Column(AqStr(128), nullable=False, default='sda')
    controller_type = Column(Enum(64, controller_types), nullable=False)

    # We need to know the bus address of each disk.
    # This isn't really nullable, but single-table inheritance means
    # that the base class will end up with the column and the base class
    # wants it to be nullable. We enforce this via __init__ instead.
    address = Column("address", AqStr(128), nullable=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='disk_machine_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    bootable = Column(Boolean(name="%s_bootable_ck" % _TN), nullable=False,
                      default=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = Column(String(255), nullable=True)

    # The order_by here ensures that machine templates always list the
    # disks in the same order.  Technically order is irrelevant in the
    # template since the disks are stored in a hash but this helps with
    # the tests and with preventing spurious re-writes.
    machine = relation(Machine, backref=backref('disks', cascade='all',
                                                order_by=[device_name]))

    __mapper_args__ = {'polymorphic_on': disk_type}

    def __repr__(self):
        # The default __repr__() is too long
        return "<%s %s (%s) of machine %s, %d GB>" % \
            (self._get_class_label(), self.device_name, self.controller_type,
             self.machine.label, self.capacity)


disk = Disk.__table__  # pylint: disable=C0103
disk.primary_key.name = '%s_pk' % _TN
disk.append_constraint(UniqueConstraint('machine_id', 'device_name',
                                        name='disk_mach_dev_name_uk'))
disk.info['unique_fields'] = ['machine', 'device_name']


class LocalDisk(Disk):
    __mapper_args__ = {'polymorphic_identity': 'local'}
