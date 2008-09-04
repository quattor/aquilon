#!/ms/dist/python/PROJ/core/2.5.0/bin/python

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        Index, ForeignKey, PassiveDefault, UniqueConstraint)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.net.dns_domain     import DnsDomain

class AName(Base):
    __tablename__ = 'a_name'

    id = Column(Integer, Sequence('a_name_seq'), primary_key=True)

    name = Column(String(64), nullable=False)

    dns_domain_id = Column(Integer,
                           ForeignKey(DnsDomain.c.id,
                                               name = 'a_name_dns_domain_fk'),
                       nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable = False))
    comments = deferred(Column(String(255)))

    dns_domain = relation(DnsDomain, uselist = False)

    def _fqdn(self):
        return '.'.join([str(self.name),str(self.dns_domain.name)])
    fqdn = property(_fqdn)


a_name = AName.__table__
a_name.primary_key.name = 'a_name_pk'

a_name.append_constraint(UniqueConstraint('name', name='a_name_uk'))

Index('a_name_dns_domain_idx',a_name.c.dns_domain_id)

table = a_name

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

