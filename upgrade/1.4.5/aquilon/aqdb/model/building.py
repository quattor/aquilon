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
""" Building is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location


class Building(Location):
    """ Building is a subtype of location """
    __tablename__ = 'building'
    __mapper_args__ = {'polymorphic_identity' : 'building'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='building_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

building = Building.__table__
building.primary_key.name='building_pk'

table = building

def populate(sess, *args, **kw):

    if len(sess.query(Building).all()) > 0:
        return

    from aquilon.aqdb.model import City

    log = kw['log']
    assert log, "no log in kwargs for Building.populate()"
    dsdb = kw['dsdb']
    assert dsdb, "No dsdb in kwargs for Building.populate()"

    city = {}
    for c in sess.query(City).all():
        city[c.name] = c

    for row in dsdb.dump('building'):
        try:
            p = city[str(row[2])]
        except KeyError, e:
            log.error(str(e))
            continue

        a = Building(name = str(row[0]),
                    fullname = str(row[1]),
                    parent = city[str(row[2])])
        sess.add(a)
    sess.commit()
    log.debug('created %s buildings'%(len(sess.query(Building).all())))



