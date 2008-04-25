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

model = Table('model',meta,
    Column('id', Integer, Sequence('model_id_seq'), primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('vendor_id', Integer, ForeignKey('vendor.id')),
    Column('hardware_type_id', Integer, ForeignKey('hardware_type.id')),
    #TODO: rethink the nullable thing(subtype hardware type with machine_type)
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)))
model.create(checkfirst=True)

class Model(aqdbBase):
    """ Model is a combination of vendor and product name used to
        catalogue various different kinds of hardware """
    @optional_comments
    def __init__(self,name,vndr,h_typ):
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

    def __repr__(self):
        return '%s %s'%(self.vendor.name,self.name)

mapper(Model,model,properties={
    'vendor':relation(Vendor),
    'hardware_type':relation(HardwareType),
    'creation_date':deferred(model.c.creation_date),
    'comments': deferred(model.c.comments)})

disk_type=mk_type_table('disk_type')
disk_type.create(checkfirst=True)

class DiskType(aqdbType):
    """ Disk Type: scsi, ccis, sata, etc. """
    pass

mapper(DiskType,disk_type,properties={
    'creation_date':deferred(disk_type.c.creation_date),
    'comments':deferred(disk_type.c.comments)})

machine = Table('machine', meta,
    Column('id', Integer, Sequence('machine_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True), #nodename
    Column('location_id', Integer, ForeignKey('location.id')),
    Column('model_id', Integer, ForeignKey('model.id')),
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
        return str(self.model.hardware_type)

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
        print "Populating vendor"
        import configuration as cfg
        from aquilon import const
        #get all dir names immediately under template-king/hardware/*/
        d=os.path.join(str(const.cfg_base),'hardware')
        created=[]
        for i in os.listdir(d):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(d,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(j)
                    try:
                        Session.save(a)
                    except Exception,e:
                        Session.rollback()
                        print >> sys.stderr, e
                        continue
                    created.append(j)
        try:
            Session.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            Session.close()

def populate_hardware_type():
    if empty(hardware_type):
        print "Populating hardware_type"
        fill_type_table(hardware_type,['rackmount', 'blade', 'workstation',
                                       'disk','cpu','nic','ram'])
def populate_disk_type():
    if empty(disk_type):
        print 'Populating disk_type'
        import configuration as cfg
        from aquilon import const
        d=os.path.join(const.cfg_base,'hardware/harddisk/generic')
        disk_types=[]
        for i in os.listdir(d):
            #disk_types.append(i.rstrip('.tpl').strip())
            disk_types.append(os.path.splitext(i)[0])
        fill_type_table(disk_type,disk_types)
        print 'created disk types %s'%(disk_types)

def populate_machines():
    s = Session()
    mlist=s.query(Model).all()

    if not mlist:
        print "Populating model table"

        v_cache = gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(HardwareType).all():
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
            ['sun','ultra-10','workstation'],
            ['dell','poweredge_6850','rackmount'],
            ['dell','poweredge_6650', 'rackmount'],
            ['dell','poweredge_2650','rackmount'],
            ['dell','poweredge_2850','rackmount'],
            ['dell','optiplex_260','workstation']]

        for i in f:
            m=Model(i[1],v_cache[i[0]],hwt_cache[i[2]])
            print m
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
    populate_machines()
    populate_disk_type()
