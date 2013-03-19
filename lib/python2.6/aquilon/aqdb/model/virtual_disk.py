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
