#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The tables/objects/mappings related to configuration in aquilon """


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.cfg.tld import Tld
from aquilon.aqdb.db_factory import db_factory, Base
from aquilon.aqdb.column_types.aqstr import AqStr


class CfgPath(Base):
    __tablename__ = 'cfg_path'

    id            = Column(Integer, Sequence('cfg_path_seq'), primary_key=True)
    tld_id        = Column(Integer, ForeignKey(
        'tld.id', name = 'cfg_path_tld_fk'), nullable=False)
    relative_path = Column(AqStr(255), nullable=False)
    last_used     = Column(DateTime, default=datetime.now)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable = False ))
    comments      = deferred(Column(String(255), nullable = True))
    tld           = relation(Tld, lazy = False)

    def __str__(self):
        return '%s/%s'%(self.tld,self.relative_path)
    def __repr__(self):
        return '%s/%s'%(self.tld,self.relative_path)

cfg_path = CfgPath.__table__
cfg_path.primary_key.name = 'cfg_path_pk'

cfg_path.append_constraint(
    UniqueConstraint('tld_id','relative_path',name='cfg_path_uk'))

Index('cfg_relative_path_idx', cfg_path.c.relative_path)

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import debug
    dbf = db_factory()
    Base.metadata.bind = dbf.engine

    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    cfg_path.create(checkfirst = True)

    cfg_base = dbf.config.get("broker", "kingdir")
    assert(cfg_base)

    #in case user's config doesn't have one...
    if not cfg_base.endswith('/'):
        cfg_base += '/'


    if len(s.query(CfgPath).all()) < 1:
        for root, dirs, files in os.walk(cfg_base):
            if ".git" in dirs:
                dirs.remove(".git")

            if root == cfg_base:
                continue

            tail = root.replace(cfg_base, "", 1)
            debug(tail)

            # Treat everything under aquilon as equivalent to a tld.
            # It might be better to have an archetype attribute on
            # the cfgpath...
            if tail == "aquilon":
                continue
            if tail.startswith("aquilon/"):
                tail = tail.replace("aquilon/", "", 1)
            (tld, slash, relative_path) = tail.partition("/")
            if not slash:
                continue
            if 'verbose' in args:
                print tld, relative_path

            try:
                dbtld = s.query(Tld).filter_by(type=tld).one()
                f = CfgPath(tld=dbtld,relative_path=relative_path)
                s.add(f)
            except Exception, e:
                sys.stderr.write(e)
                s.rollback()
                continue

        s.commit()
        print 'created %s cfg_paths'%(len(s.query(CfgPath).all()))

    b=s.query(CfgPath).first()
    assert(b)
    assert(b.tld)


    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
