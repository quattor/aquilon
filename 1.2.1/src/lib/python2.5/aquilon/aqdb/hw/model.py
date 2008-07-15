#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Vendor and Model are representations of the various manufacturers and
    the asset inventory of the kinds of machines we use in the plant """


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
from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.table_types.name_table import make_name_class
from aquilon.aqdb.hw.vendor import Vendor


class Model(Base):
    __tablename__ = 'model'
    id = Column(Integer, Sequence('model_id_seq'), primary_key=True)
    name = Column(String(64), unique=True, index=True)
    vendor_id = Column(Integer,
                       ForeignKey('vendor.id', name = 'model_vendor_fk'),
                       nullable = False)
    machine_type = Column(AqStr(16), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments = deferred(Column(String(255)))

    vendor = relation(Vendor)

model = Model.__table__
model.primary_key.name = 'model_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    model.create(checkfirst = True)

    mlist=s.query(Model).all()

    if not mlist:


        f = [['ibm', 'hs20','blade'],
            ['ibm', 'ls20','blade'],
            ['ibm','hs21','blade'],
            ['ibm','hs40','blade'],
            ['hp','bl35p','blade'],
            ['hp','bl465c','blade'],
            ['hp','bl480c','blade'],
            ['hp','bl680c','blade'],
            ['hp','bl685c','blade'],
            ['hp','dl145','rackmount'],
            ['hp','dl580','rackmount'],
            ['hp','bl45p','blade'],
            ['hp','bl260c','blade'],
            ['verari', 'vb1205xm', 'blade'],
            ['sun','ultra-10','workstation'],
            ['dell','poweredge_6850','rackmount'],
            ['dell','poweredge_6650', 'rackmount'],
            ['dell','poweredge_2650','rackmount'],
            ['dell','poweredge_2850','rackmount'],
            ['dell','optiplex_260','workstation']]

        for i in f:
            m = Model(name = i[1],
                      vendor = s.query(Vendor).filter_by(name =i[0]).first(),
                      machine_type = i[2])
            s.add(m)
        try:
            s.commit()
        except Exception,e:
            print e
        finally:
            s.close()

    print s.query(Model).all()

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
