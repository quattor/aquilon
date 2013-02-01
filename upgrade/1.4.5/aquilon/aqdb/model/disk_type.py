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
""" For the various types of disks we use """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr


_ABV = 'disk_type'
_disk_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash']


class DiskType(Base):
    """ Disk Type: scsi, cciss, sata, etc. """
    __tablename__  = _ABV

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    type = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

disk_type = DiskType.__table__
table = DiskType.__table__

disk_type.primary_key.name='%s_pk'%(_ABV)
disk_type.append_constraint(UniqueConstraint('type',name='%s_uk'%(_ABV)))


def populate(sess, *args, **kw):
    if len(sess.query(DiskType).all()) < 1:
        for t in _disk_types:
            dt = DiskType(type = t)
            sess.add(dt)
        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

    dt = sess.query(DiskType).first()
    assert(dt)


