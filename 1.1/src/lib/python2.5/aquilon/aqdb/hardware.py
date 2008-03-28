#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""The tables/objects/mappings related to hardware in Aquilon. """

if __name__ == '__main__':
    from sys import path
    path.append('../..')

#from DB import meta, engine, Session, aqdbBase
#from aquilon.aqdb.utils.debug import ipshell
#from aquilon.aqdb.utils.schemahelpers import *
from DB import *
from utils.schemahelpers import *

from sqlalchemy import *
from sqlalchemy.orm import *

vendor = mk_name_id_table('vendor',meta)
vendor.create(checkfirst=True)
class Vendor(aqdbBase):
    pass
mapper(Vendor,vendor,properties={
    'creation_date':deferred(vendor.c.creation_date)})

hardware_type = mk_type_table('hardware_type', meta)
hardware_type.create(checkfirst=True)

class HardwareType(aqdbType):
    pass
mapper(HardwareType,hardware_type,properties={
    'creation_date':deferred(hardware_type.c.creation_date)})

#model format: rackmount, blade, workstation
model_format=mk_type_table('model_format', meta)
model_format.create(checkfirst=True)

class ModelFormat(aqdbType):
    pass

mapper(ModelFormat,model_format, properties={
    'format':synonym(model_format.c.type),
    'creation_date':deferred(model_format.c.creation_date)})

model = Table('model',meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('vendor_id', Integer,
           ForeignKey('vendor.id', ondelete='RESTRICT')),
    Column('model_format_id', Integer,
           ForeignKey('model_format.id', ondelete='RESTRICT')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)))
model.create(checkfirst=True)

class Model(aqdbBase):
    def __init__(self,name,vndr,form):
        self.name = name.lower().strip()

        if isinstance(vndr,Vendor):
            self.vendor = vndr
        elif isinstance(vndr,str):
            s = Session()
            try:
                self.vendor = s.query(Vendor).filter_by(name=vndr).one()
            except NoSuchRowException:
                print "Can not find vendor '%s'"%(vndr)
                return
            except Exception, e:
                print 'ERROR: Unhandled Exception',
                print e
                return
            finally:
                s.close()
        else:
            raise ArgumentError("Incorrect vendor specification '%s'",vndr)
            return
        #TODO: add string check as well, too tired for it now
        if isinstance(form,ModelFormat):
            self.model_format = form
        else:
            raise ArgumentError("Incorrect format specification '%s'",form)
            return
    def __repr__(self):
        return '%s %s'%(self.vendor.name,self.name)

mapper(Model,model,properties={
    'vendor':relation(Vendor),
    'model_format':relation(ModelFormat),
    'creation_date':deferred(model.c.creation_date),
    'comments': deferred(model.c.comments)})

if __name__ == '__main__':

    if empty(vendor,engine):
        s = Session()
        for i in ['sun','ibm','hp','dell','intel','amd','broadcom', 'generic']:
            a=Vendor(i)
            s.save(a)
        s.commit()
        s.close()

    if empty(hardware_type,engine):
        fill_type_table(hardware_type,['model','disk','cpu','nic','ram'])

    if empty(model_format,engine):
        fill_type_table(model_format,['rackmount', 'blade', 'workstation'])


    if empty(model,engine):
        s=Session()
        v_cache=gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(ModelFormat).all():
            hwt_cache[str(c)] = c

        f = [['ibm','hs20','blade'],
            ['hp','ls41','blade'],
            ['sun','ultra-10','workstation'],
            ['dell','poweredge-6850','rackmount'],
            ['dell','optiplex-260','workstation']]

        for i in f:
            m=Model(i[1],v_cache[i[0]],hwt_cache[i[2]])
            s.save_or_update(m)
        try:
            s.commit()
        except Exception,e:
            print e
        finally:
            s.close()
