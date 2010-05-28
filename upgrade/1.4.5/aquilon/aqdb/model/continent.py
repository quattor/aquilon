# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" Continent is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location


class Continent(Location):
    """ Continent is a subtype of location """
    __tablename__ = 'continent'
    __mapper_args__ = {'polymorphic_identity':'continent'}
    id = Column(Integer, ForeignKey('location.id',
                                    name='continent_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

continent = Continent.__table__
continent.primary_key.name='continent_pk'

table = continent

def populate(sess, *args, **kw):

    _continents = ('af', 'as', 'au', 'eu', 'na', 'sa')

    if len(sess.query(Continent).all()) < len(_continents):
        from aquilon.aqdb.model import Hub

        hubs ={}
        for hub in sess.query(Hub).all():
            hubs[hub.name] = hub
        a = Continent(name='af', fullname='Africa', parent = hubs['ln'])
        b = Continent(name='as', fullname='Asia', parent = hubs['hk'])
        c = Continent(name='au', fullname='Australia', parent = hubs['hk'])
        d = Continent(name='eu', fullname='Europe', parent = hubs['ln'])
        e = Continent(name='na', fullname='North America', parent = hubs['ny'])
        f = Continent(name='sa', fullname='South America', parent = hubs['ny'])

        for i in (a,b,c,d,e,f):
            sess.add(i)
        sess.commit()



