# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" The module governing tables and objects that represent IP networks in
    Aquilon."""

#TODO: nullable location id.
#TODO: nullable description column?
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Location
from aquilon.aqdb.column_types.aqstr import AqStr


_TN = 'dns_domain'

class DnsDomain(Base):
    """ For Dns Domain names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    def __str__(self):
        return str(self.name)


dns_domain = DnsDomain.__table__
table = DnsDomain.__table__


dns_domain.primary_key.name='%s_pk'%(_TN)
dns_domain.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))

def populate(sess, *args, **kw):

    if len(sess.query(DnsDomain).all()) < 1:

        ms   = DnsDomain(name='ms.com')#,
                         #audit_info = kw['audit_info'])

        onyp = DnsDomain(name='one-nyp.ms.com',
                         #audit_info = kw['audit_info'])
                         comments = '1 NYP test domain')

        devin1 = DnsDomain(name='devin1.ms.com',
                           #audit_info = kw['audit_info'])
                           comments='43881 Devin Shafron Drive domain')

        theha = DnsDomain(name='the-ha.ms.com',
                          #audit_info = kw['audit_info'])
                          comments='HA domain')

        for i in (ms, onyp, devin1, theha):
            sess.add(i)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e


