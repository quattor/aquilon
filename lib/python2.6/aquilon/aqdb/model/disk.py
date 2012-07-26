# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
""" Polymorphic representation of disks which may be local, nas or san """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, column_property, deferred, synonym
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import Base, Machine, ServiceInstance
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.config import Config

disk_types = ['local', 'nas', 'san', 'virtual_disk']
controller_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash',
                    'fibrechannel']

_TN = 'disk'
_NDTN = 'nas_disk'


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

    """
    We need to know the bus address of each disk.
    This isn't really nullable, but single-table inheritance means
    that the base class will end up with the column and the base class
    wants it to be nullable. We enforce this via __init__ instead.
    """
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


class NasDisk(Disk):
    """
        Network attached disks required for root diskless machines, primarily
        for virtual machines whose images are hosted on NFS shares. In the case
        of ESX these are mounted by the host OS, not the guest OS.
    """
    __mapper_args__ = {'polymorphic_identity': 'nas'}

    """
        No cascade delete here: we want to restrict any attempt to delete
        any service instance that has client dependencies.
    """
    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='%s_srv_inst_fk' % (
                                                        _NDTN)),
                                 nullable=True)

#    TODO: double check property values on forward and backrefs before commit
#        cascade ops too
    service_instance = relation(ServiceInstance, backref='nas_disks')

    def __init__(self, **kw):
        if 'address' not in kw or kw['address'] is None:
            raise ValueError("address is mandatory for nas disks")
        super(NasDisk, self).__init__(**kw)

    def __repr__(self):
        return "<%s %s (%s) of machine %s, %d GB, provided by %s>" % \
                (self._get_class_label(), self.device_name,
                 self.controller_type, self.machine.label, self.capacity,
                 self.service_instance.name)


# The formatter code is interested in the count of disks/machines, and it is
# cheaper to query the DB than to load all entities into memory
ServiceInstance.nas_disk_count = column_property(
    select([func.count()],
           NasDisk.service_instance_id == ServiceInstance.id)
    .label("nas_disk_count"), deferred=True)

ServiceInstance.nas_machine_count = column_property(
    select([func.count(func.distinct(NasDisk.machine_id))],
           NasDisk.service_instance_id == ServiceInstance.id)
    .label("nas_machine_count"), deferred=True)

#machine_specs-> indicates the service instance for nas disk
#service instance name is the share name

#max_shares to metacluster


# Utility functions for service / resource based disk mounts

# This should come from some external API...?
def find_storage_data(dbshare):
    """
    Scan a storeng-style data file, checking each line as we go

    Storeng-style data files are blocks of data. Each block starts
    with a comment describing the fields for all subsequent lines. A
    block can start at any time. Fields are separated by '|'.
    This function will invoke the function after parsing every data
    line. The function will be called with a dict of the fields. If the
    function returns True, then we stop scanning the file, else we continue
    on until there is nothing left to parse.

    dbshare can be a Share or a ServiceInstance which is a nas_disk_share
    """

    # TODO should check here 
    # isinstance(dbshare, PlenaryResource and dbshare.type == share)
    # or (isinstance(dbshare, PlenaryInstanceNasDiskShare)

    config = Config()
    with open(config.get("broker", "sharedata")) as datafile:
        share_info = {"server": None, "mount": None}

        def check_nas_line(info):
            """
            Search for the pshare info that refers to this plenary
            """
            # silently discard lines that don't have all of our reqd info.
            for k in ["objtype", "pshare", "server", "dg"]:
                if k not in info:
                    return False

            if info["objtype"] == "pshare" and info["pshare"] == dbshare.name:
                share_info["server"] = info["server"]
                share_info["mount"] = "/vol/%(dg)s/%(pshare)s" % (info)

                return True
            else:
                return False

        for line in datafile:
            line = line.rstrip()

            if line[0] == '#':
                # A header line
                hdr = line[1:].split('|')
            else:
                fields = line.split('|')
                if len(fields) == len(hdr):  # silently ignore invalid lines
                    info = dict()
                    for i in range(0, len(hdr)):
                        info[hdr[i]] = fields[i]

                    if check_nas_line(info):
                        break

        return share_info

