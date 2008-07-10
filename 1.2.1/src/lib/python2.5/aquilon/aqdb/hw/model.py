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

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

import depends
from sqlalchemy import (MetaData, create_engine, UniqueConstraint, Table,
                        Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, PassiveDefault)
from sqlalchemy.orm import relation, deferred

from column_types.aqstr import AqStr
from db_factory import Base
from table_types.name_table import make_name_class
from vendor import Vendor

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

def populate():
    #FIX ME
    s = Session()
    mlist=s.query(Model).all()

    if not mlist:
        print "Populating model table"

        v_cache = gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(MachineType).all():
            hwt_cache[str(c)] = c

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
            m=Model(i[1],v_cache[i[0]],hwt_cache[i[2]])
            s.save(m)
        try:
            s.commit()
        except Exception,e:
            print e
        finally:
            s.close()
