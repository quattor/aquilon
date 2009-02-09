""" The high level configuration elements in use """

import os
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.base               import Base
from aquilon.aqdb.column_types.aqstr import AqStr
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_ABV = 'tld'
_PRECEDENCE = 71


class Tld(Base):
    """ Configuration Top Level Directory or 'cfg_tld' are the high level
            namespace categories and live as the directories in template-king:

            aquilon   (the only archetype for now)
            os        (major types (linux,solaris) prefabricated)
            hardware  (vendors + types prefabricated)
            services
            feature
            personality
    """
    __tablename__  = 'tld'

    id             = Column(Integer, Sequence('%s_seq'%_ABV), primary_key=True)
    type           = Column('type', AqStr(32), nullable=False)
    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))
#    audit_info_id  = deferred(Column(Integer, ForeignKey('audit_info.id',
#                         name = '%s_audit_info_fk'%(_ABV)), nullable = False))

#    audit_info     = relation(AuditInfo)

    def __str__(self):
        return str(self.type)

tld   = Tld.__table__
table = Tld.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

tld.primary_key.name = 'tld_pk'
tld.append_constraint(UniqueConstraint('type', name='tld_uk'))

def populate(sess, **kw):
    if len(sess.query(Tld).all()) > 0:
        return

    cfg_base = kw['cfg_base']
    assert os.path.isdir(cfg_base)

    tlds=[]
    for i in os.listdir(cfg_base):
        p = os.path.abspath(os.path.join(cfg_base, i))
        if os.path.isdir(p):
            # Hack to consider all subdirectories of the archetype
            # as a tld.
            if i == "aquilon":
                for j in os.listdir(p):
                    if os.path.isdir(os.path.abspath(os.path.join(p, j))):
                        tlds.append(j)
            elif i == ".git":
                continue
            else:
                tlds.append(i)

    for i in tlds:
        t =Tld(type=i)#, audit_info=kw['audit_info'])
        sess.add(t)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a=sess.query(Tld).first()
    assert(a)

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

"""
    def __eq__(self,other):
        if isinstance(other,str):
            if self.type == other:
                return True
            else:
                return False
        else:
            raise ArgumentError('Can only be compared to strings')
"""
