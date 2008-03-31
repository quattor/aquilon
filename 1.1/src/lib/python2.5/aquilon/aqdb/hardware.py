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
from aquilon.aqdb.utils.schemahelpers import *
from aquilon import const

from location import Location,Chassis
from configuration import CfgPath

location=Table('location',meta,autoload=True)
chassis=Table('chassis',meta,autoload=True)
cfg_path=Table('cfg_path',meta, autoload=True)

from sqlalchemy import Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

const.tables=['vendor','hardware_type','machine_type','model','machine']
#machine, machine_type, hardware_type, model, vendor

def parse_template(file):
    """ Reads in a quattor hardware template and returns a dictionary
        of all the key/value pairs within it.
    """
    if not file.startswith(const.nic_directory):
        fqp = const.nic_directory + file
    else:
        fqp=file
        import os
        (pth,file) = os.path.split(file)

    f = open(fqp,'ro')
    hash={}
    hash['cfg_path']=file

    for line in f.readlines():
        if line.isspace() or line.startswith('#'):
            continue
        if line.startswith('structure template '):
            continue

        line = line.strip().strip(';').rstrip('\n')
        line = line.replace('"','')
        (a,b,c) = line.partition('=')
        hash[a.strip()] = c.strip()
    return hash


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
    Column('id', Integer, primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('vendor_id', Integer,
           ForeignKey('vendor.id', ondelete='RESTRICT')),
    Column('hardware_type_id', Integer,
           ForeignKey('hardware_type.id', ondelete='RESTRICT')),
    Column('machine_type_id', Integer,
           ForeignKey('machine_type.id', ondelete='RESTRICT'),nullable=True),
    #TODO: rethink the nullable thing(subtype hardware type with machine_type)
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)))
model.create(checkfirst=True)

class Model(aqdbBase):
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
            raise ArgumentError("Incorrect vendor specification '%s'",vndr)
            return
        #TODO: handle string arguments?
        if isinstance(h_typ,HardwareType):
            self.hardware_type = h_typ
        else:
            raise ArgumentError("Incorrect hardware type specified '%s'",h_typ)
            return
        if m_typ:
            if isinstance(m_typ,MachineType):
                self.machine_type = m_typ
            else:
                raise ArgumentError("Incorrect machine type specified '%s'",
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
    Column('location_id', Integer, ForeignKey('location.id',
                                              ondelete='RESTRICT',
                                              onupdate='CASCADE')),
    Column('model_id', Integer, ForeignKey('model.id',
                                           ondelete='RESTRICT',
                                           onupdate='CASCADE')),
    Column('machine_type_id', Integer, ForeignKey('machine_type.id',
                                                  ondelete='RESTRICT',
                                                  onupdate='CASCADE')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
machine.create(checkfirst=True)

class Machine(aqdbBase):
    """ Represents any kind of computer that we need to model. This spans
        workstations, rackmount or chassis servers.
    """
    def __init__(self,loc,model,**kw):
        self.location = loc
        if kw.has_key('name'):
            self.name=kw.pop('name')
        #if loc is a chassis, then get the node #
        #if loc is a rack, get node #
        #desk: dunno, could take a building i guess as a hack for now
        #might also be nice to take building, then validate ask for more
        #info based on what machine_type it is
        self.model = model
        #TODO: ALOT!!!
        #automatic node name assignment (building, rack, chassis)
        #create rack and chassis by building name and #, Chassis w/ chassis #
        #what are the nodenames of rackmount boxes? (how to autocalculate?)
        #sysloc on everything
        #attributes on all location nodes for each parent loc component
        #check whether this model type can go in this location
        #IMPORTANT:
        #chassis needs to have slots. And machines can have node #s? (simplify
        #   the methods for naming machines, etc.)
    def __repr__(self):
        return 'Machine: %s is a %s located in %s'%(
            self.name,self.model,self.location)
    def type(self):
        return str(self.model.machine_type)

mapper(Machine,machine, properties={
    'location': relation(Location),
    'model':    relation(Model),
    #type is m.model.machine_type. would be nice to have it directly
    'creation_date' : deferred(machine.c.creation_date),
    'comments': deferred(machine.c.comments)
})

def populate_vendor():
    if empty(vendor,engine):
        s = Session()
        for i in ['sun','ibm','hp','dell','intel','amd','broadcom', 'generic']:
            a=Vendor(i)
            s.save(a)
        s.commit()
        s.close()

def populate_hardware_type():
    if empty(hardware_type,engine):
        fill_type_table(hardware_type,['machine','disk','cpu','nic','ram'])

def populate_machine_type():
    if empty(machine_type,engine):
        fill_type_table(machine_type,['rackmount', 'blade', 'workstation'])

def populate_model():
    if empty(model,engine):
        s=Session()
        v_cache=gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(HardwareType).all():
            hwt_cache[str(c)] = c

        m_cache={}
        for t in s.query(MachineType).all():
            m_cache[str(t)] = t

        f = [['ibm','hs20','machine','blade'],
            ['ibm','ls20','machine','blade'],
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
            ['dell','poweredge-6850','machine','rackmount'],
            ['dell','optiplex-260','machine','workstation']]

        for i in f:
            m=Model(i[1],v_cache[i[0]],hwt_cache[i[2]],m_cache[i[3]])
            s.merge(m)
        try:
            s.commit()
        except Exception,e:
            print e
        finally:
            s.close()

def populate_fake_machine():
    if empty(machine,engine):

        c=Session.query(Chassis).first()
        mod=Session.query(Model).filter_by(name='hs20').one()
        m=Machine(c,mod)

        Session.save(m)
        Session.commit()

def populate_np_nodes():
    s=Session
    mod=Session.query(Model).filter_by(name='hs20').one()
    with open('etc/np-nodes','r') as f:
        for line in f.readlines():
            (c,q,num)=line.strip().lstrip('n').partition('n')
            c='n'+c
            try:
                r=s.query(Chassis).filter_by(name=c).one()
            except Exception,e:
                print 'no such chassis %s'%c
                continue
            m=Machine(r,mod,name=line.strip())
            s.save(m)
    s.commit()

if __name__ == '__main__':
    from aquilon.aqdb.utils.debug import ipshell

    populate_vendor()
    populate_hardware_type()
    populate_machine_type()
    populate_model()
    populate_fake_machine()
    populate_np_nodes()

    #ipshell()




#do we need hardware type when we have nic, cpu, disk and model tables?
#machine is an association map of all these items
