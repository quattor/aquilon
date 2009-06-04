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
""" Country is a subclass of Location """

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location

class Country(Location):
    """ Country is a subtype of location """
    __tablename__ = 'country'
    __mapper_args__ = {'polymorphic_identity':'country'}
    id = Column(Integer,ForeignKey('location.id',
                                   name='country_loc_fk',
                                   ondelete='CASCADE'),
                primary_key=True)

country = Country.__table__
country.primary_key.name='country_pk'

table = country

def populate(sess, *args, **kw):
    if len(sess.query(Country).all()) < 1:
        from aquilon.aqdb.model import Continent, Hub

        log = kw['log']
        assert log, "no log in kwargs for Country.populate()"
        dsdb = kw['dsdb']
        assert dsdb, "No dsdb in kwargs for Country.populate()"

        cnts = {}

        for c in sess.query(Continent).all():
            cnts[c.name] = c

        for row in dsdb.dump('country'):

            a = Country(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = cnts[str(row[2])])
            sess.add(a)

        sess.commit()

        try:
            sess.commit()
        except Exception, e:
            log.error(str(e))

        log.debug('created %s countries'%(len(sess.query(Country).all())))


