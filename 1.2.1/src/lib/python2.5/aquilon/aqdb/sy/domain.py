#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" For Systems and related objects """
from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.sy.quattor_server import QuattorServer
from aquilon.aqdb.auth.user_principal import UserPrincipal, user_principal
from aquilon.aqdb.net.dns_domain import DnsDomain, dns_domain


class Domain(Base):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories """
    __tablename__ = 'domain'
    id = Column(Integer, Sequence('domain_seq'), primary_key = True)
    name = Column(AqStr(32), nullable = False)
    server_id = Column(Integer,
                       ForeignKey('quattor_server.id', name = 'domain_qs_fk'),
                       nullable = False)
    compiler = Column(String(255), nullable = False, default =
                      '/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc')
    owner_id = Column(Integer, ForeignKey(
        'user_principal.id', name = 'domain_user_princ_fk'), nullable = False)

    creation_date = deferred(Column( DateTime, default=datetime.now,
                                    nullable = False))
    comments      = deferred(Column('comments', String(255), nullable=True))

    server        = relation(QuattorServer, backref = 'domains')
    owner         = relation(UserPrincipal, uselist = False, backref = 'domain')

domain = Domain.__table__
domain.primary_key.name = 'domain_pk'
domain.append_constraint(
    UniqueConstraint('name',name='domain_uk'))

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    domain.create(checkfirst = True)

    if len(s.query(Domain).all()) < 1:
        qs = s.query(QuattorServer).first()
        cdb = s.query(UserPrincipal).filter_by(name = 'cdb').one()
        daqscott = s.query(UserPrincipal).filter_by(name='daqscott').one()

        p = Domain(name = 'production', server = qs, owner = cdb,
                   comments='The master production area')
        q = Domain(name = 'daqscott', server = qs, owner = daqscott)

        s.add(p)
        s.add(q)
        s.commit()
        d=s.query(Domain).first()
        assert(d)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
