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
""" an element of a list of location types """
from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, LocationSearchList
from aquilon.aqdb.column_types.aqstr import AqStr


class SearchListItem(Base):
    """ Association object for location types to various lists for
        searching against service mapping. """

    __tablename__ = 'search_list_item'

    id = Column('id', Integer, Sequence('sli_seq'), primary_key=True)

    location_search_list_id = Column(Integer, ForeignKey('location_search_list.id',
                                                         name='sli_list_fk',
                                                         ondelete='CASCADE'),
                                     nullable=False)

    location_type = Column(AqStr(32), nullable=False)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    lsl = relation(LocationSearchList)
#TODO: add better str and repr methods:
#In [20]: sli1
#Out[20]: SearchListItem instance <--- should read 'chassis'


search_list_item = SearchListItem.__table__

search_list_item.primary_key.name='search_li_pk'

search_list_item.append_constraint(
    UniqueConstraint('id', 'location_type', name='sli_loc_typ_uk'))

search_list_item.append_constraint(
    UniqueConstraint('location_type', 'position',
                     name='sli_loc_typ_pos_uk'))

LocationSearchList.location_types = relation(SearchListItem,
                          collection_class = ordering_list('position'),
                            order_by = [SearchListItem.__table__.c.position])

table = search_list_item

def populate(sess, *args, **kw):

    m = sess.query(LocationSearchList).first()
    assert m

    if len(sess.query(SearchListItem).all()) < 1:

        sli1 = SearchListItem(location_type = 'chassis', lsl = m, position = 1)
        sli2 = SearchListItem(location_type = 'rack', lsl = m, position = 2)
        sli3 = SearchListItem(location_type = 'building', lsl = m, position = 3)
        sli4 = SearchListItem(location_type = 'city', lsl = m, position = 4)
        sli5 = SearchListItem(location_type = 'country', lsl = m, position = 5)
        sli6 = SearchListItem(location_type = 'continent', lsl = m, position = 6)
        sli7 = SearchListItem(location_type = 'hub', lsl = m, position = 7)
        sli8 = SearchListItem(location_type = 'world', lsl = m, position = 8)

        for i in (sli1, sli2, sli3, sli4, sli5, sli6, sli7):
            sess.add(i)
            sess.commit()

    cnt = len(sess.query(SearchListItem).all())
    assert cnt > 6





