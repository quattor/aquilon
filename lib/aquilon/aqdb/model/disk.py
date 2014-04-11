# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Polymorphic representation of disks which may be local or san """

from datetime import datetime
import re

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred, validates

from aquilon.exceptions_ import ArgumentError
from aquilon.utils import force_wwn
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.aqdb.model import Base, Machine, DeviceLinkMixin

# FIXME: this list should not be hardcoded here
controller_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash',
                    'fibrechannel']

_TN = 'disk'


class Disk(DeviceLinkMixin, Base):
    """
        Base Class for polymorphic representation of disk or disk-like resources
    """
    __tablename__ = _TN
    _instance_label = 'device_name'

    _address_re = re.compile(r"(?:\d+:){3}\d+$")

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    disk_type = Column(String(64), nullable=False)
    capacity = Column(Integer, nullable=False)
    device_name = Column(AqStr(128), nullable=False, default='sda')
    controller_type = Column(Enum(64, controller_types), nullable=False)

    address = Column(AqStr(16), nullable=True)
    wwn = Column(AqStr(32), nullable=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='%s_machine_fk' % _TN,
                                            ondelete='CASCADE'),
                        nullable=False)

    bootable = Column(Boolean(name="%s_bootable_ck" % _TN), nullable=False,
                      default=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    machine = relation(Machine, innerjoin=True,
                       backref=backref('disks', cascade='all'))

    __table_args__ = (UniqueConstraint(machine_id, device_name,
                                       name='%s_mach_dev_name_uk' % _TN),
                      UniqueConstraint(wwn, name='%s_wwn_uk' % _TN))
    __mapper_args__ = {'polymorphic_on': disk_type,
                       'with_polymorphic': '*'}

    def __repr__(self):
        # The default __repr__() is too long
        return "<%s %s (%s) of machine %s, %d GB>" % \
            (self._get_class_label(), self.device_name, self.controller_type,
             self.machine.label, self.capacity)

    @validates('address')
    def validate_address(self, key, value):  # pylint: disable=W0613
        if not value:
            return None
        if not self._address_re.match(value):
            raise ArgumentError("Disk address '%s' is not valid, it must "
                                "match %s." % (value, self._address_re.pattern))
        return value

    @validates('wwn')
    def validate_wwn(self, key, value):
        return force_wwn(key, value)

    # Currently this is for curiosity only. It would be more useful if we could
    # look up the vendor name somewhere, based on the OUI.
    def oui(self):  # pragma: no cover
        if not self.wwn:
            return None
        # IEEE 803.2
        if self.wwn[0] == '1' or self.wwn[0] == '2':
            return self.wwn[4:10]
        # IEEE registered name
        if self.wwn[0] == '5' or self.wwn[0] == '6':
            return self.wwn[1:7]
        # Mapped EUI-64
        if self.wwn[0] in set(['c', 'd', 'e', 'f']):
            # The first byte contains bits 18-23 of the OUI, plus the NAA
            oui_18_23 = int(self.wwn[0:2], 16)
            # Mask the NAA
            oui_18_23 = oui_18_23 & 63
            # Bits 16-17 are assumed to be 0
            oui_18_23 = oui_18_23 * 4
            return "%02x" % oui_18_23 + self.wwn[2:6]

        # Unknown WWN format
        return None

disk = Disk.__table__  # pylint: disable=C0103
disk.info['unique_fields'] = ['machine', 'device_name']


class LocalDisk(Disk):
    __mapper_args__ = {'polymorphic_identity': 'local'}
