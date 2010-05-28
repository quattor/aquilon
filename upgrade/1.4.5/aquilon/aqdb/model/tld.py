# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

