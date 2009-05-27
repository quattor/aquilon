""" Lists of location types that define search ordering (as an algorithm).
    Intended for use with service maps during automated instance selection """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'lsl'
_PRECEDENCE = 50

class LocationSearchList(Base):
    """ Lists of location types that define search ordering (as an algorithm).
    Intended for use with service maps during automated instance selection """

    __tablename__ = 'location_search_list'

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key = True)

    name = Column(AqStr(32), nullable = False)

    creation_date = Column(DateTime, default = datetime.now,
                                    nullable = False )
    comments      = Column(String(255), nullable = True)

#    audit_info_id   = deferred(Column(Integer, ForeignKey(
#            'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
#                                      nullable = False))

#    audit_info = relation(AuditInfo)

location_search_list = LocationSearchList.__table__
table                = LocationSearchList.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

location_search_list.primary_key.name = 'loc_search_list_pk'
location_search_list.append_constraint(
    UniqueConstraint('name', name='location_search_list_uk'))
# This would appear to be the new naming convention... not renaming without
# a migration plan, though.
#    UniqueConstraint('name', name='%s_uk' % (_ABV)))

def populate(sess, *args, **kw):

    if len(sess.query(LocationSearchList).all()) < 1:
        #ai = sess.query(AuditInfo).filter_by(id=1).one()
        #assert ai

        #l = LocationSearchList(name = 'full', audit_info = kw['audit_info'])
        l = LocationSearchList(name = 'full')
        sess.add(l)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

    m = sess.query(LocationSearchList).first()
    assert m


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
