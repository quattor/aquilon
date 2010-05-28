# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" The tables/objects/mappings related to configuration in aquilon """

import os
import sys
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Tld
from aquilon.aqdb.column_types.aqstr import AqStr

class CfgPath(Base):
    __tablename__ = 'cfg_path'

    id = Column(Integer, Sequence('cfg_path_id_seq'), primary_key=True)

    tld_id = Column(Integer, ForeignKey('tld.id', name='cfg_path_tld_fk'),
                    nullable=False)

    relative_path = Column(AqStr(255), nullable=False)
    last_used = Column(DateTime, default=datetime.now)
    creation_date = Column(DateTime, default=datetime.now, nullable=False )
    comments = Column(String(255), nullable=True)

    tld = relation(Tld, lazy=False)

    def __str__(self):
        return '%s/%s'%(self.tld,self.relative_path)
    def __repr__(self):
        return '%s/%s'%(self.tld,self.relative_path)

cfg_path = CfgPath.__table__
cfg_path.primary_key.name='cfg_path_pk'

cfg_path.append_constraint(
    UniqueConstraint('tld_id','relative_path',name='cfg_path_uk'))

Index('cfg_relative_path_idx', cfg_path.c.relative_path)

table = cfg_path

def populate(sess, *args, **kw):
    if len(sess.query(CfgPath).all()) > 0:
        return

    log = kw['log']

    cfg_base = kw['cfg_base']
    assert os.path.isdir(cfg_base), "no cfg path supplied"

    #in case user's config doesn't have one...
    if not cfg_base.endswith('/'):
        cfg_base += '/'

    removes = ('.git', 'personality', 't')

    for root, dirs, files in os.walk(cfg_base):
        for r in removes:
            if r in dirs:
                dirs.remove(r)

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
            msg = str(e) + ' for tld '+ tld
            log.error(msg)
            sess.rollback()
            continue

    sess.commit()
    log.debug('created %s cfg_paths'%(len(sess.query(CfgPath).all())))

    b=sess.query(CfgPath).first()
    assert(b)
    assert(b.tld)



