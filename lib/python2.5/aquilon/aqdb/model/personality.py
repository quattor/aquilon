""" Personality as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.sql import select
from sqlalchemy.orm import relation, deferred
from sqlalchemy.orm.session import object_session

from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'prsnlty'
_TN  = 'personality'
_PRECEDENCE = 71


class Personality(Base):
    """ Personality names """
    __tablename__  = _TN

    id   = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name = '%s_arch_fk'%(_ABV)), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments      = Column(String(255), nullable=True)

    archetype = relation(Archetype, backref="personality", uselist=False)

    def __repr__(self):
        s = ("<"+self.__class__.__name__ + " name ='"+ self.name +
             "', " + str(self.archetype) +'>')
        return s

    @classmethod
    def by_archetype(cls, dbarchetype):
        session = object_session(dbarchetype)
        return session.query(cls).filter(
            cls.__dict__['archetype'] == dbarchetype).all()


personality = Personality.__table__
table       = Personality.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

personality.primary_key.name = '%s_pk'%(_ABV)
personality.append_constraint(UniqueConstraint('name', 'archetype_id',
                                               name='%s_uk'%(_TN)))

def populate(sess, *args, **kw):
    if len(sess.query(Personality).all()) > 0:
        return

    import os

    cfg_base = kw['cfg_base']
    assert os.path.isdir(cfg_base), "No such directory '%s'"%(cfg_base)

    for arch in sess.query(Archetype).all():
        #find aquilon archetype and all directories under it
        #change if we grow past having multiple archtypes w/ personalities
        if arch.name == 'aquilon':
            p = os.path.join(cfg_base, arch.name, 'personality')
            assert os.path.isdir(p), \
                    "Can't find personality directory '%s' in populate" % p
            for i in os.listdir(p):
                if os.path.isdir(os.path.abspath(os.path.join(p, i))):
                    pers = Personality(name=i, archetype=arch)
                    sess.add(pers)
        else:
            pers = Personality(name='generic', archetype=arch)
            sess.add(pers)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(Personality).first()
    assert(a)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
