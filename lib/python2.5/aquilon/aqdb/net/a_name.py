#!/ms/dist/python/PROJ/core/2.5.0/bin/python

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (MetaData, create_engine, UniqueConstraint, Table,
                        Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, PassiveDefault)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.net.dns_domain     import DnsDomain

class AName(Base):
    __tablename__ = 'a_name'

    id = Column(Integer, Sequence('a_name_seq'), primary_key=True)

    name = Column(String(64), primary_key=True)

    dns_domain_id = Column(Integer,
                           ForeignKey(DnsDomain.c.id,
                                               name = 'a_name_dns_domain_fk'),
                       primary_key = True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable = False))
    comments = deferred(Column(String(255)))

    dns_domain = relation(DnsDomain, uselist = False)

a_name = AName.__table__
a_name.primary_key.name = 'a_name_pk'

table = a_name

