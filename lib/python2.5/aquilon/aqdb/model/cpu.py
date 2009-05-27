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
    id            = Column(Integer, Sequence('cpu_id_seq'), primary_key = True)
    name          = Column(AqStr(64), nullable = False)
    vendor_id     = Column(Integer, ForeignKey(
        'vendor.id', name = 'cpu_vendor_fk'), nullable = False)
    speed         = Column(Integer, nullable = False)
    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False ))
    comments      = deferred(Column(String(255), nullable = True))
    vendor        = relation(Vendor)

cpu = Cpu.__table__
cpu.primary_key.name = 'cpu_pk'

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
            sess.add(a)
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

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
