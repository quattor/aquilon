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
