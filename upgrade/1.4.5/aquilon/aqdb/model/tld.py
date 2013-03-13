# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" The high level configuration elements in use """

import os
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'tld'


class Tld(Base):
    """ Configuration Top Level Directory or 'cfg_tld' are the high level
            namespace categories and live as the directories in template-king:

            aquilon   (the only archetype for now)
            os        (major types (linux,solaris) prefabricated)
            hardware  (vendors + types prefabricated)
            services
            feature
            personality
    """
    __tablename__  = 'tld'

    id = Column(Integer, Sequence('%s_seq'%_ABV), primary_key=True)
    type = Column('type', AqStr(32), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    def __str__(self):
        return str(self.type)

tld   = Tld.__table__
table = Tld.__table__


tld.primary_key.name='tld_pk'
tld.append_constraint(UniqueConstraint('type', name='tld_uk'))

def populate(sess, **kw):
    if len(sess.query(Tld).all()) > 0:
        return

    cfg_base = kw['cfg_base']
    assert os.path.isdir(cfg_base)
    skip = ('.git', 'personality')

    tlds=[]
    for i in os.listdir(cfg_base):
        p = os.path.abspath(os.path.join(cfg_base, i))
        if os.path.isdir(p):
            # Hack to consider all subdirectories of the archetype
            # as a tld.
            if i == "aquilon":
                for j in os.listdir(p):
                    if os.path.isdir(os.path.abspath(os.path.join(p, j))):
                        tlds.append(j)
            elif i in skip:
                continue
            else:
                tlds.append(i)

    for i in tlds:
        t =Tld(type=i)
        sess.add(t)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a=sess.query(Tld).first()
    assert(a)

#

