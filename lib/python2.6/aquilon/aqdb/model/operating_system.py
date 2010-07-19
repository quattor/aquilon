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
""" Operating System as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation
from sqlalchemy.orm.session import object_session

from aquilon.utils import monkeypatch
from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_TN  = 'operating_system'
_ABV = 'os'

class OperatingSystem(Base):
    """ Operating Systems """
    __tablename__  = _TN
    _class_label = 'Operating System'

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    version = Column(AqStr(16), nullable=False )
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name='%s_arch_fk'%(_ABV)), nullable=False)
    #vendor id?
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, backref='os', uselist=False, lazy=False)

    def __format__(self, format_spec):
        if format_spec and format_spec[-1] == 'l':
            clsname = self.__class__._get_class_label(tolower=True)
            format_spec = format_spec[:-1]
        else:
            clsname = self.__class__._get_class_label()
        val = "%s %s/%s-%s" % (clsname, self.archetype.name, self.name, self.version)
        return val.__format__(format_spec)

    @property
    def cfg_path(self):
        return 'os/%s/%s'% (self.name, self.version)

    @classmethod
    def by_archetype(cls, dbarchetype):
        session = object_session(dbarchetype)
        return session.query(cls).filter(
            cls.__dict__['archetype'] == dbarchetype).all()


operating_system = OperatingSystem.__table__

operating_system.primary_key.name = '%s_pk'% (_ABV)
operating_system.append_constraint(
    UniqueConstraint('name', 'version', 'archetype_id', name='%s_uk'% (_TN)))
operating_system.info['unique_fields'] = ['name', 'version', 'archetype']


@monkeypatch(operating_system)
def populate(sess, *args, **kw):
    if len(sess.query(OperatingSystem).all()) > 0:
        return

    aquilon = Archetype.get_by('name', 'aquilon', sess)[0]
    for ver in ['4.0.1-ia32', '4.0.1-x86_64', '5.0-x86_64']:
        os_obj = OperatingSystem(archetype=aquilon, name='linux', version=ver)
        sess.add(os_obj)

    aurora = Archetype.get_unique(sess, 'aurora')
    for ver in ['3.0.3-ia32','3.0.3-amd64', '4.0.1-ia32', '4.0.1-x86_64',
                '4.0.2-ia32', '4.0.2-x86_64', '5.0-x86_64', 'generic']:
        os_obj = OperatingSystem(archetype=aurora, name='linux', version=ver)
        sess.add(os_obj)

    win = Archetype.get_unique(sess, 'windows')
    win_obj=OperatingSystem(archetype=win, name='windows', version='generic')
    sess.add(win_obj)

    vmhost = Archetype.get_unique(sess, 'vmhost')
    for ver in ['4.0.0']:
        os_obj = OperatingSystem(archetype=vmhost, name='esxi', version=ver)
        sess.add(os_obj)

    pserver = Archetype.get_unique(sess, 'pserver')
    assert pserver, "can't find archetype 'pserver' in os.populate"
    os_obj = OperatingSystem(archetype=pserver, name='ontap',
                             version = '7.3.1p2d20')
    sess.add(os_obj)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(OperatingSystem).first()
    assert a, "No operating system created by populate"
