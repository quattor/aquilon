# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
""" Manufacturer names """
import os
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Tld
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'vendor'

class Vendor(Base):
    """ Vendor names """
    __tablename__  = _ABV

    id = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False))
    comments = deferred(Column(String(255), nullable=True))

vendor = Vendor.__table__
table = Vendor.__table__

table.info['abrev']      = _ABV

vendor.primary_key.name='%s_pk'%(_ABV)
vendor.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))

def populate(sess, **kw):

    if len(sess.query(Vendor).all()) < 1:
        import cfg_path as cfg
        created = []

        cfg_base = kw['cfg_base']
        assert os.path.isdir(cfg_base)

        #in case user's config doesn't have one...
        if not cfg_base.endswith('/'):
            cfg_base += '/'
        cfg_base += 'hardware'

        for i in os.listdir(cfg_base):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(cfg_base,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(name=j)
                    try:
                        sess.add(a)
                    except Exception,e:
                        sess.rollback()
                        sys.stderr.write(e)
                        continue
                    created.append(j)

        for v in ['bnt', 'cisco', 'virtual', 'aurora_vendor']:
            if not v in created:
                dbv = Vendor(name=v)
                try:
                    sess.add(dbv)
                except Exception, e:
                    sess.rollback()
                    raise e
                created.append(v)

        try:
            sess.commit()
        except Exception,e:
            raise e
        finally:
            sess.close()

        if 'log' in locals():
            log.INFO('created %s vendors'%(len(created)))
