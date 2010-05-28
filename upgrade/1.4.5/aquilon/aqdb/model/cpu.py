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
""" If you can read this you should be documenting """
from __future__ import with_statement
from datetime   import datetime
import os

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.aqdb.model import Base, Vendor
from aquilon.aqdb.column_types.aqstr import AqStr


class Cpu(Base):
    __tablename__ = 'cpu'
    id = Column(Integer, Sequence('cpu_id_seq'), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor.id',
                                           name='cpu_vendor_fk'),
                       nullable=False)

    speed = Column(Integer, nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False ))
    comments = deferred(Column(String(255), nullable=True))
    vendor = relation(Vendor)

cpu = Cpu.__table__
cpu.primary_key.name='cpu_pk'

cpu.append_constraint(
    UniqueConstraint('vendor_id','name','speed', name='cpu_nm_speed_uk'))

table = cpu

def populate(sess, *args, **kw):

    if len(sess.query(Cpu).all()) < 1:
        import re
        m=re.compile('speed')

        cfg_base = kw['cfg_base']
        assert os.path.isdir(cfg_base), "no cfg path supplied"

        log = kw['log']

        #get all dir names immediately under template-king/hardware/cpu/
        base=os.path.join(str(cfg_base),'hardware/cpu')
        cpus=[]

        for i in os.listdir(base):
            for j in os.listdir(os.path.join(base,i)):
                name = j.rstrip('.tpl').strip()
                with open(os.path.join(base,i,j),'r') as f:
                    assert(m)
                    for line in f.readlines():
                        a_match=m.search(line)
                        if a_match:
                            l,e,freq=line.partition('=')
                            assert(isinstance(freq,str))
                            speed=re.sub('\*MHz','',freq.strip().rstrip(';'))
                            #TODO: better checking if freq is ok here
                            if speed.isdigit():
                                cpus.append([i,name,speed])
                                break
                            else:
                                Assert(False)
                    f.close()

        for vendor,name,speed in cpus:
            kw={}
            vendor=sess.query(Vendor).filter_by(name=vendor).first()

            assert(vendor)
            assert(name)
            assert(speed)

            if vendor:
                kw['vendor'] = vendor
                kw['name']   = name
                kw['speed']  = int(speed)

                a=Cpu(**kw)

                assert(isinstance(a,Cpu))

                try:
                    sess.add(a)
                except Exception,e:
                    sess.rollback()
                    log.error(str(e))
                    continue
            else:
                log.error("CREATE CPU: cant find vendor '%s'"%(vendor))

        try:
            av = sess.query(Vendor).filter_by(name='aurora_vendor').one()
            a = Cpu(vendor=av, name='aurora_cpu', speed=0,
                    comments='Placeholder Aurora CPU type.')
            vv = Vendor.get_unique(sess, 'virtual')
            vc = Cpu(vendor=vv, name='virtual_cpu', speed=0)
            sess.add_all([a, vc])
        except Exception, e:
            sess.rollback()
            log.error(str(e))

        try:
            sess.commit()
        except Exception,e:
            sess.rollback()
            log.error(str(e))




        cnt = len(sess.query(Cpu).all())
        log.debug('created %s cpus'%(cnt))
