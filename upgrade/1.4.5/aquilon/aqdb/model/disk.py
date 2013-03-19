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
""" Polymorphic representation of disks which may be local, nas or san """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Machine, ServiceInstance
from aquilon.aqdb.column_types import AqStr, Enum

disk_types = ['local', 'nas', 'san']
controller_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash']

_TN = 'disk'
class Disk(Base):
    """
        Base Class for polymorphic representation of disk or disk-like resources
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq'% (_TN)), primary_key=True)
    disk_type = Column(Enum(64, disk_types), nullable=False)
    capacity = Column(Integer, nullable=False)
    device_name = Column(AqStr(128), nullable=False, default='sda')
    controller_type = Column(Enum(64, controller_types), nullable=False)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='disk_machine_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    machine = relation(Machine, backref=backref('disks', cascade='all'))

    __mapper_args__ = {'polymorphic_on': disk_type}

    def __repr__(self):
        return '%s <machine %s %s /dev/%s %s GB> '% (self.__class__.__name__,
                                          self.machine.name,
                                          self.controller_type,
                                          self.device_name,
                                          self.capacity)

disk = Disk.__table__
disk.primary_key.name='%s_pk'% (_TN)
disk.append_constraint(UniqueConstraint('machine_id', 'device_name',
                                        name='disk_mach_dev_name_uk'))
table = disk

class LocalDisk(Disk):
    __mapper_args__ = {'polymorphic_identity': 'local'}


_NDTN = 'nas_disk'
class NasDisk(Disk):
    """
        Network attached disks required for root diskless machines, primarily
        for virtual machines whose images are hosted on NFS shares. In the case
        of ESX these are mounted by the host OS, not the guest OS.
    """
    __mapper_args__ = {'polymorphic_identity': 'nas'}

    """
    We need to know the bus address of each disk.
    This isn't really nullable, but single-table inheritance means
    that the base class will end up with the column and the base class
    wants it to be nullable. We enforce this via __init__ instead.
    """
    address = Column(AqStr(128), nullable=True)

    """
        No cascade delete here: we want to restrict any attempt to delete
        any service instance that has client dependencies.
    """
    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='%s_srv_inst_fk'% (
                                                        _NDTN)),
                                 nullable=True)

#    TODO: double check property values on forward and backrefs before commit
#        cascade ops too
    service_instance = relation(ServiceInstance, backref='nas_disks')

    def __init__(self, **kw):
        if 'address' not in kw:
            raise ValueError("address is mandatory for nas disks")
        super(NasDisk, self).__init__(**kw)

    def __repr__(self):
        return '%s <machine %s %s /dev/%s %s GB provided by %s> '% (
            self.__class__.__name__,
            self.machine.name,
            self.controller_type,
            self.device_name,
            self.capacity,
            self.service_instance.name)

#machine_specs-> indicates the service instance for nas disk
#service instance name is the share name

#max_shares to metacluster
