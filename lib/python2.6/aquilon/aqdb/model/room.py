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
""" Room is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.utils import monkeypatch
from aquilon.aqdb.model import Location, Building


class Room(Location):
    """ Room is a subtype of location """
    __tablename__ = 'room'
    __mapper_args__ = {'polymorphic_identity' : 'room'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='room_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

room = Room.__table__
room.primary_key.name = 'room_pk'
room.info['unique_fields'] = ['name']


@monkeypatch(room)
def populate(sess, **kwargs):
    """Populate skeleton database with some room information."""

    if len(sess.query(Room).all()) > 0:
        return

    if sess.query(Building).count() < 1:
        Building.populate(sess, **kw)

    devin1 = Building.get_unique(sess, 'dd')
    if devin1:
        pod3 = Room(name='ddroom3', fullname='Devin Pod 3', parent=devin1)
        sess.add(pod3)
    sess.commit()
