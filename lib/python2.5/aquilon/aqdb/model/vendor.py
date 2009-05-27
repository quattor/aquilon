""" Manufacturer names """
import os
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Tld
from aquilon.aqdb.column_types.aqstr import AqStr
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_ABV = 'vendor'
_PRECEDENCE = 50

class Vendor(Base):
    """ Vendor names """
    __tablename__  = _ABV

    id   = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key = True)
    name = Column(AqStr(32), nullable = False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                        nullable = False ))
    comments      = deferred(Column(String(255), nullable = True))

#    audit_info_id   = deferred(Column(Integer, ForeignKey(
#            'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
#                                      nullable = False))

#    audit_info = relation(AuditInfo)

    #def __str__(self):
    #    return str(self.name)

vendor = Vendor.__table__
table  = Vendor.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

vendor.primary_key.name = '%s_pk'%(_ABV)
vendor.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))

def populate(sess, **kw):

    if len(sess.query(Vendor).all()) < 1:
        import cfg_path as cfg
        created = []

        #ai = kw['audit_info']

        cfg_base = kw['cfg_base']
        assert os.path.isdir(cfg_base)

        #in case user's config doesn't have one...
        if not cfg_base.endswith('/'):
            cfg_base += '/'
        cfg_base += 'hardware'

        for i in os.listdir(cfg_base):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(cfg_base,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(name=j)#, audit_info=kw['audit_info'])
                    try:
                        sess.add(a)
                    except Exception,e:
                        sess.rollback()
                        sys.stderr.write(e)
                        continue
                    created.append(j)

        aurora_vendor = Vendor(name='aurora_vendor',
                               #audit_info=kw['audit_info'])
                             comments='Placeholder vendor for Aurora hardware.')

        sess.add(aurora_vendor)
        created.append(aurora_vendor)

        for v in ['bnt', 'cisco']:
            if not v in created:
                dbv = Vendor(name=v)#, audit_info=kw['audit_info'])
                try:
                    sess.add(dbv)
                except Exception, e:
                    sess.rollback()
                    raise e
                created.append(v)

        try:
            sess.commit()
        except Exception,e:
            raise e
        finally:
            sess.close()

        if 'log' in locals():
            log.INFO('created %s vendors'%(len(created)))



# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
