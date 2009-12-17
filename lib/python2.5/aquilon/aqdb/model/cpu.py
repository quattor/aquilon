# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
""" If you can read this you should be documenting """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Vendor
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'cpu'

cpus = [['amd', 'opteron_2212', '2000'],
        ['amd', 'opteron_2216', '2400'],
        ['amd', 'opteron_2218', '2600'],
        ['amd', 'opteron_248', '2200'],
        ['amd', 'opteron_250', '2400'],
        ['amd', 'opteron_2600', '2600'],
        ['amd', 'opteron_275', '2200'],
        ['amd', 'opteron_280', '2400'],
        ['intel', 'pentium_2660', '2600'],
        ['intel', 'core_duo', '2000'],
        ['intel', 'l5420', 2500],
        ['intel', 'woodcrest_2300', 2300],
        ['intel', 'woodcrest_2660', 2660],
        ['intel', 'xeon_2500', 2500],
        ['intel', 'xeon_2660', 2660],
        ['intel', 'xeon_3000', 3000],
        ['intel', 'xeon_3100', 3100],
        ['intel', 'xeon_3400', 3400],
        ['intel', 'xeon_3600', 3600],
        ['sun', 'ultrasparc_iii_i_1300', 1300],
        ['sun', 'ultrasparc_iii_i_1600', 1600],
        ['aurora_vendor', 'aurora_cpu', 0],
        ['virtual', 'virtual_cpu', 0]]


class Cpu(Base):
    """ Cpus with vendor, model name and speed (in MHz) """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % (_TN)), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor.id',
                                           name='cpu_vendor_fk'),
                       nullable=False)

    speed = Column(Integer, nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    vendor = relation(Vendor)

cpu = Cpu.__table__
cpu.primary_key.name = '%s_pk' % _TN

cpu.append_constraint(
    UniqueConstraint('vendor_id', 'name', 'speed', name='%s_nm_speed_uk' % _TN))

table = cpu


def populate(sess, *args, **kw):
    """ Populate some well known cpus for testing """

    if len(sess.query(Cpu).all()) < 1:

        log = kw['log']

        for vendor, name, speed in cpus:

            vendor = sess.query(Vendor).filter_by(name=vendor).first()
            assert vendor, "No vendor found for '%s'" % vendor

            a = Cpu(vendor=vendor, name=name, speed=speed)
            sess.add(a)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            log.error(str(e))

        cnt = len(sess.query(Cpu).all())
        log.debug('created %s cpus' % cnt)
