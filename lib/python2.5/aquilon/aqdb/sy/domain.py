""" Configuration Domains for Systems """

from datetime import datetime

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
    id = Column(Integer, Sequence('domain_id_seq'), primary_key = True)
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

table = domain

def populate(sess, *args, **kw):

    if len(sess.query(Domain).all()) < 1:
        qs = sess.query(QuattorServer).first()
        assert(qs)

        cdb = sess.query(UserPrincipal).filter_by(name = 'cdb').one()
        assert(cdb)

        daqscott = sess.query(UserPrincipal).filter_by(name='daqscott').one()
        assert(daqscott)

        q = Domain(name = 'daqscott', server = qs, owner = daqscott)

        r = Domain(name = 'ny-prod', server = qs, owner = cdb,
                   comments='The NY regional production domain')

        sess.add(q)
        sess.add(r)
        sess.commit()

        d=sess.query(Domain).first()
        assert(d)




# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
