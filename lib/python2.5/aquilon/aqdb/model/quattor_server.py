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
""" At the moment, quattor servers are exposed as a very dull
    sublass of System """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import System

class QuattorServer(System):
    __tablename__ = 'quattor_server'

    id = Column(Integer,
                ForeignKey('system.id', ondelete='CASCADE',
                           name='qs_system_fk'), primary_key=True)

    system = relation(System, uselist=False, backref='quattor_server')
    __mapper_args__ = {'polymorphic_identity' : 'quattor_server'}

quattor_server = QuattorServer.__table__
quattor_server.primary_key.name='qs_pk'

table = quattor_server

def populate(sess, *args, **kw):
    if len(sess.query(QuattorServer).all()) < 1:
        from dns_domain import DnsDomain

        dom = sess.query(DnsDomain).filter_by(name='ms.com').one()
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


