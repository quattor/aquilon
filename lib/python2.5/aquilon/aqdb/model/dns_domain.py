""" The module governing tables and objects that represent IP networks in
    Aquilon."""

#TODO: nullable location id.
#TODO: nullable description column?
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Location
from aquilon.aqdb.column_types.aqstr import AqStr


_TN = 'dns_domain'

class DnsDomain(Base):
    """ For Dns Domain names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    def __str__(self):
        return str(self.name)


dns_domain = DnsDomain.__table__
table = DnsDomain.__table__


dns_domain.primary_key.name='%s_pk'%(_TN)
dns_domain.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))

def populate(sess, *args, **kw):

    if len(sess.query(DnsDomain).all()) < 1:

        ms   = DnsDomain(name='ms.com')#,
                         #audit_info = kw['audit_info'])

        onyp = DnsDomain(name='one-nyp.ms.com',
                         #audit_info = kw['audit_info'])
                         comments = '1 NYP test domain')

        devin1 = DnsDomain(name='devin1.ms.com',
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
