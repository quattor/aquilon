""" The module governing tables and objects that represent IP networks in
    Aquilon."""

#TODO: nullable location id.
#TODO: nullable description column?
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.base               import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.loc.location       import Location
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_ABV = 'dns_domain'
_PRECEDENCE = 62

class DnsDomain(Base):
    """ For Dns Domain names """
    __tablename__  = _ABV

    id   = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key = True)
    name = Column(AqStr(32), nullable = False)

    creation_date = Column(DateTime, default = datetime.now,
                                    nullable = False )
    comments      = Column(String(255), nullable = True)

#    audit_info_id   = deferred(Column(Integer, ForeignKey(
#            'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
#                                      nullable = False))

#    audit_info = relation(AuditInfo)

    def __str__(self):
        return str(self.name)


dns_domain = DnsDomain.__table__
table      = DnsDomain.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

dns_domain.primary_key.name = '%s_pk'%(_ABV)
dns_domain.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))

def populate(sess, *args, **kw):

    if len(sess.query(DnsDomain).all()) < 1:

        ms   = DnsDomain(name = 'ms.com')#,
                         #audit_info = kw['audit_info'])

        onyp = DnsDomain(name = 'one-nyp.ms.com',
                         #audit_info = kw['audit_info'])
                         comments = '1 NYP test domain')

        devin1 = DnsDomain(name = 'devin1.ms.com',
                           #audit_info = kw['audit_info'])
                           comments='43881 Devin Shafron Drive domain')

        theha = DnsDomain(name='the-ha.ms.com',
                          #audit_info = kw['audit_info'])
                          comments='HA domain')

        for i in (ms, onyp, devin1, theha):
            sess.add(i)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
