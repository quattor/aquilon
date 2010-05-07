# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
""" Personality as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.utils import monkeypatch
from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'prsnlty'
_TN = 'personality'


class Personality(Base):
    """ Personality names """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % (_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name='%s_arch_fk' % (_ABV)), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, backref='personality', uselist=False)

    services = association_proxy('_services', 'service')

    def __repr__(self):
        s = ("<" + self.__class__.__name__ + " name ='" + self.name +
             "', " + str(self.archetype) + '>')
        return s

    @classmethod
    def by_archetype(cls, dbarchetype):
        session = object_session(dbarchetype)
        return session.query(cls).filter(
            cls.__dict__['archetype'] == dbarchetype).all()


personality = Personality.__table__
table = Personality.__table__

personality.primary_key.name = '%s_pk' % (_ABV)
personality.append_constraint(UniqueConstraint('name', 'archetype_id',
                                               name='%s_uk' % (_TN)))

generics = ['aquilon', 'windows', 'aurora', 'aegis', 'vmhost', 'pserver']

aquilon_personalities = ['c1_regbas_qa', 'c1_rs_grid', 'compileserver',
                         'cva-ice20-qa', 'cva-ice20', 'desktopserver',
                         'fxoption-nyriskprod-qa', 'fxoption-nyriskprod',
                         'ied-rvtesting', 'ied-scenprod', 'ied-testgrid',
                         'infra', 'inventory', 'lemon-collector-oracle',
                         'db2-test', 'ied-prodgrid', 'spg-shared-qa',
                         'spg-shared-va', 'unixeng-test', 'zcs', 'ifmx-test',
                         'aqd-testing', 'spg-rmi', 'sybase-test', 'train-prod',
                         'train-tu']


@monkeypatch(personality)
def populate(sess, **kw):
    if len(sess.query(Personality).all()) > 0:
        return

    for arch in generics:
        archetype = sess.query(Archetype).filter_by(name=arch).first()
        assert archetype, "No archetype found for '%s' in populate" % arch
        pers = Personality(name='generic', archetype=archetype)
        sess.add(pers)

    aquln = sess.query(Archetype).filter_by(name='aquilon').first()
    assert aquln, "No aquilon archetype found in personality populate"

    for nm in aquilon_personalities:
        pers = Personality(archetype=aquln, name=nm)
        sess.add(pers)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(Personality).first()
    assert(a)
