""" The tables/objects/mappings related to configuration in aquilon """

import os
import sys
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.cfg.tld            import Tld
from aquilon.aqdb.base import Base
from aquilon.aqdb.column_types.aqstr import AqStr

class CfgPath(Base):
    __tablename__ = 'cfg_path'

    id            = Column(Integer,
                           Sequence('cfg_path_id_seq'), primary_key=True)

    tld_id        = Column(Integer, ForeignKey('tld.id',
                                      name = 'cfg_path_tld_fk'), nullable=False)

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

table = cfg_path

def populate(db, *args, **kw):
    sess = db.Session()
    if len(sess.query(CfgPath).all()) > 0:
        return

    cfg_base = db.config.get("broker", "kingdir")
    assert os.path.isdir(cfg_base)

    #in case user's config doesn't have one...
    if not cfg_base.endswith('/'):
        cfg_base += '/'

    for root, dirs, files in os.walk(cfg_base):
        if ".git" in dirs:
            dirs.remove(".git")

        if root == cfg_base:
            continue

        tail = root.replace(cfg_base, "", 1)

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
        try:
            dbtld = sess.query(Tld).filter_by(type=tld).one()
            f = CfgPath(tld=dbtld,relative_path=relative_path)
            sess.add(f)
        except Exception, e:
            sys.stderr.write(e)
            sess.rollback()
            continue

    sess.commit()
    print 'created %s cfg_paths'%(len(sess.query(CfgPath).all()))

    b=sess.query(CfgPath).first()
    assert(b)
    assert(b.tld)


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
