# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Disk for share """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref, column_property, deferred
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import Disk, Share


_TN = 'disk'


# Disk subclass for Share class
class VirtualDisk(Disk):
    """To be done"""
    __mapper_args__ = {'polymorphic_identity': 'virtual_disk'}

    share_id = Column(Integer, ForeignKey('share.id',
                                                    name='%s_share_fk' % _TN,
                                                    ondelete='CASCADE'),
                                nullable=True)

    share = relation(Share, innerjoin=True,
                     backref=backref('disks', cascade='all'))

    def __init__(self, **kw):
        if 'address' not in kw or kw['address'] is None:
            raise ValueError("address is mandatory for shared disks")
        super(VirtualDisk, self).__init__(**kw)

    def __repr__(self):
        return "<%s %s (%s) of machine %s, %d GB, provided by %s>" % \
                (self._get_class_label(), self.device_name,
                 self.controller_type, self.machine.label, self.capacity,
                 (self.share.name if self.share else "no_share"))

# The formatter code is interested in the count of disks/machines, and it is
# cheaper to query the DB than to load all entities into memory
Share.disk_count = column_property(
    select([func.count()],
           VirtualDisk.share_id == Share.id)
    .label("disk_count"), deferred=True)

Share.machine_count = column_property(
    select([func.count(func.distinct(VirtualDisk.machine_id))],
           VirtualDisk.share_id == Share.id)
    .label("machine_count"), deferred=True)
