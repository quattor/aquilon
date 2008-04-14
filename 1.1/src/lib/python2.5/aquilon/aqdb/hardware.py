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
from __future__ import with_statement

import sys
sys.path.append('../..')

import os
import datetime

from db import *

from location import Location,Chassis
from configuration import CfgPath

location=Table('location',meta,autoload=True)
chassis=Table('chassis',meta,autoload=True)
cfg_path=Table('cfg_path',meta, autoload=True)

from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.exceptions_ import ArgumentError,NoSuchRowException

vendor = mk_name_id_table('vendor',meta)
vendor.create(checkfirst=True)
class Vendor(aqdbBase):
    pass

mapper(Vendor,vendor,properties={
    'creation_date':deferred(vendor.c.creation_date),
    'comments':deferred(vendor.c.comments)})


#cpu/ram/disk/nic
hardware_type = mk_type_table('hardware_type', meta)
hardware_type.create(checkfirst=True)

class HardwareType(aqdbType):
    """ Hardware Type is one of cpu/ram/disk/nic """
    pass
mapper(HardwareType,hardware_type,properties={
    'creation_date':deferred(hardware_type.c.creation_date),
    'comments':deferred(hardware_type.c.comments)})

#machine type: rackmount, blade, workstation
machine_type=mk_type_table('machine_type', meta)
machine_type.create(checkfirst=True)

class MachineType(aqdbType):
    pass

mapper(MachineType,machine_type, properties={
    'creation_date':deferred(machine_type.c.creation_date),
    'comments':deferred(machine_type.c.comments)})

model = Table('model',meta,
    Column('id', Integer, Sequence('model_id_seq'), primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('vendor_id', Integer, ForeignKey('vendor.id')),
    Column('hardware_type_id', Integer, ForeignKey('hardware_type.id')),
    Column('machine_type_id', Integer, ForeignKey('machine_type.id'), nullable=True),
    #TODO: rethink the nullable thing(subtype hardware type with machine_type)
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)))
model.create(checkfirst=True)

class Model(aqdbBase):
    """ Model is a combination of vendor and product name used to
        catalogue various different kinds of hardware """
    @optional_comments
    def __init__(self,name,vndr,h_typ,m_typ=None):
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
            raise ArgumentError("Incorrect vendor specification '%s'" % vndr)
            return
        #TODO: handle string arguments?
        if isinstance(h_typ,HardwareType):
            self.hardware_type = h_typ
        else:
            raise ArgumentError("Incorrect hardware type specified '%s'" %
                    h_typ)
            return
        if m_typ:
            if isinstance(m_typ,MachineType):
                self.machine_type = m_typ
            else:
                raise ArgumentError("Incorrect machine type specified '%s'" %
                                    m_typ)
                return
    def __repr__(self):
        return '%s %s'%(self.vendor.name,self.name)

mapper(Model,model,properties={
    'vendor':relation(Vendor),
    'hardware_type':relation(HardwareType),
    'machine_type':relation(MachineType),
    'creation_date':deferred(model.c.creation_date),
    'comments': deferred(model.c.comments)})

""" Machine is defined at this point so that physical hardware components can
    ForeignKey off machine.id, which is to become an association object
    variant of our old friend the Many to Many
"""
machine = Table('machine', meta,
    Column('id', Integer, Sequence('machine_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True), #nodename
    Column('location_id', Integer, ForeignKey('location.id')),
    Column('model_id', Integer, ForeignKey('model.id')),
    Column('machine_type_id', Integer, ForeignKey('machine_type.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
machine.create(checkfirst=True)

class Machine(aqdbBase):
    """ Represents any kind of computer that we need to model. This spans
        workstations, rackmount or chassis servers.
    """
    @optional_comments
    def __init__(self,loc,model,**kw):
        self.location = loc
        self.model = model
        #TODO: validate that this model type can go in this location type
        #TODO: make name and node#/chassis loc mutually exclusive

        if kw.has_key('name'):
            self.name=kw.pop('name')
        #if loc = chassis then get a node #
        elif str(loc.type)=='chassis':
            if kw.has_key('node'):
                if isinstance(kw['node'],int):
                    self.name= ''.join([loc.name, 'n', str(kw.pop('node'))])
                else:
                    msg="""
Argument to 'node' must be integer, got '%s', type '%s'"""%(kw['node'],
                                                               type(kw['node']))
                    raise TypeError(msg.lstrip())

        #if loc = rack/its a rackmount, nodename is faked (how is TBD),
        #  create a new unique chassis for it with 1 slot.
        #if loc = desk: TBD, building for now

    def __repr__(self):
        return 'Machine: %s is a %s located in %s'%(
            self.name,self.model,self.location)
    def type(self):
        return str(self.model.machine_type)

mapper(Machine,machine, properties={
    'location': relation(Location),
    'model':    relation(Model),
    'creation_date' : deferred(machine.c.creation_date),
    'comments': deferred(machine.c.comments)
})

status=Table('status', meta,
    Column('id', Integer, Sequence('status_id_seq'),primary_key=True),
    Column('name', String(16), unique=True, index=True, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255)))
status.create(checkfirst=True)

class Status(object):
    """ Status represents phases of deployment. can be one of prod, dev, qa, or
        build. Child of host table, so it comes first. """
    @optional_comments
    def __init__(self,name):
        msg = """
Status is a static table and cannot be instanced, only queried. """
        raise ArgumentError(msg.lstrip())
        return
    def __repr__(self):
        return str(self.name)

mapper(Status, status)
if empty(status):
    i=status.insert()
    for name in ['prod','dev','qa','build']:
        i.execute(name=name)

####POPULATION ROUTINES####
def populate_vendor():
    if empty(vendor):
        s = Session()
        for i in ['sun','ibm','hp','dell','intel','amd','broadcom', 'generic']:
            a=Vendor(i)
            s.save(a)
        s.commit()
        s.close()

def populate_hardware_type():
    if empty(hardware_type):
        fill_type_table(hardware_type,['machine','disk','cpu','nic','ram'])

def populate_machine_type():
    if empty(machine_type):
        fill_type_table(machine_type,['rackmount', 'blade', 'workstation'])

def populate_model():
    if empty(model):
        s = Session()
        v_cache = gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(HardwareType).all():
            hwt_cache[str(c)] = c

        m_cache={}
        for t in s.query(MachineType).all():
            m_cache[str(t)] = t

        f = [['ibm', 'hs20', 'machine', 'blade'],
            ['ibm', 'ls20', 'machine','blade'],
            ['ibm','hs21','machine','blade'],
            ['ibm','hs40','machine','blade'],
            ['hp','bl35p','machine','blade'],
            ['hp','bl465c','machine','blade'],
            ['hp','bl480c','machine','blade'],
            ['hp','bl680c','machine','blade'],
            ['hp','bl685c','machine','blade'],
            ['hp','dl145','machine','rackmount'],
            ['hp','dl580','machine','rackmount'],
            ['sun','ultra-10','machine','workstation'],
            ['dell','poweredge_6850','machine','rackmount'],
            ['dell','poweredge_6650', 'machine', 'rackmount'],
            ['dell','poweredge_2650','machine','rackmount'],
            ['dell','poweredge_2850','machine','rackmount'],
            ['dell','optiplex_260','machine','workstation']]

        for i in f:
            m=Model(i[1],v_cache[i[0]],hwt_cache[i[2]],m_cache[i[3]])
            s.merge(m)
        try:
            s.commit()
        except Exception,e:
            print e
        finally:
            s.close()

if __name__ == '__main__':
    populate_vendor()
    populate_hardware_type()
    populate_machine_type()
    populate_model()
