""" At the moment, quattor servers are exposed as a very dull
    sublass of System """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.sy.system import System

class QuattorServer(System):
    __tablename__ = 'quattor_server'

    id = Column(Integer,
                ForeignKey('system.id', ondelete = 'CASCADE',
                           name = 'qs_system_fk'), primary_key = True)

    system = relation(System, uselist = False, backref = 'quattor_server')
    __mapper_args__ = {'polymorphic_identity' : 'quattor_server'}

quattor_server = QuattorServer.__table__
quattor_server.primary_key.name = 'qs_pk'

table = quattor_server

def populate(sess, *args, **kw):
    if len(sess.query(QuattorServer).all()) < 1:
        from aquilon.aqdb.net.dns_domain import DnsDomain

        dom = sess.query(DnsDomain).filter_by(name = 'ms.com').one()
        assert(dom)

        qs=QuattorServer(name='oziyp2', dns_domain=dom)
        sess.add(qs)
        try:
            sess.commit()
        except Exception, e:
            print e
            sess.rollback()
            return False

    qs=sess.query(QuattorServer).filter_by(name='oziyp2').one()
    assert(qs)
    assert(qs.dns_domain)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
