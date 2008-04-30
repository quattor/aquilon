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
import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=os.path.join(LOGDIR,'aqdb.log'),
                    filemode='w')
from aquilon.exceptions_ import ArgumentError,NoSuchRowException

from location import Location,Chassis
from configuration import CfgPath

location=Table('location',meta,autoload=True)
chassis=Table('chassis',meta,autoload=True)
cfg_path=Table('cfg_path',meta, autoload=True)

from sqlalchemy import Column, Integer, Sequence, String, select
from sqlalchemy.orm import mapper, relation, deferred, backref
from sqlalchemy.sql.expression import alias

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
        e = "Status is a static table and can't be instanced, only queried."
        raise ArgumentError(e)
    def __repr__(self):
        return str(self.name)

mapper(Status, status)
if empty(status):
    i=status.insert()
    for name in ['prod','dev','qa','build']:
        i.execute(name=name)

vendor = mk_name_id_table('vendor',meta)
vendor.create(checkfirst=True)
class Vendor(aqdbBase):
    pass

mapper(Vendor,vendor,properties={
    'creation_date':deferred(vendor.c.creation_date),
    'comments':deferred(vendor.c.comments)})

machine_type = mk_type_table('machine_type', meta)
machine_type.create(checkfirst=True)

class MachineType(aqdbType):
    """ Hardware Type is one of  blade/rackmount/workstation"""
    pass
mapper(MachineType,machine_type,properties={
    'creation_date':deferred(machine_type.c.creation_date),
    'comments':deferred(machine_type.c.comments)})

model = Table('model',meta,
    Column('id', Integer, Sequence('model_id_seq'), primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('vendor_id', Integer, ForeignKey('vendor.id')),
    Column('machine_type_id', Integer,
           ForeignKey('machine_type.id'),nullable=False),
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
            except NoSuchRowExceptioncfgmst:
                print "Can not find vendor '%s'"%(vndr)
                return
            except Exception, e:
                print 'Unhandled Exception', e
                raise Exception(e)
            finally:
                s.close()
        else:
            raise ArgumentError("Incorrect vendor specification '%s'" % vndr)
        #TODO: handle string arguments?
        if isinstance(h_typ,MachineType):
            self.machine_type = h_typ
        else:
            raise ArgumentError("Incorrect hardware type specified '%s'" %
                    h_typ)

    def __repr__(self):
        return '%s %s'%(self.vendor.name,self.name)


mapper(Model,model,properties={
    'vendor'         : relation(Vendor),
    'machine_type'  : relation(MachineType),
    'creation_date'  : deferred(model.c.creation_date),
    'comments'       : deferred(model.c.comments)})

disk_type=mk_type_table('disk_type')
disk_type.create(checkfirst=True)

class DiskType(aqdbType):
    """ Disk Type: scsi, ccis, sata, etc. """
    pass

mapper(DiskType,disk_type,properties={
    'creation_date':deferred(disk_type.c.creation_date),
    'comments':deferred(disk_type.c.comments)})

cpu=Table('cpu', meta,
    Column('id', Integer, Sequence('cpu_id_seq'), primary_key=True),
    Column('name', String(64),nullable=False),
    Column('vendor_id', Integer,ForeignKey('vendor.id'),nullable=False),
    Column('speed', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('vendor_id','name','speed', name='cpu_nm_speed_uk'))
cpu.create(checkfirst=True)

class Cpu(aqdbBase):
    @optional_comments
    def __init__(self,*args,**kw):
        if kw['vendor'] and isinstance(kw['vendor'],Vendor):
            self.vendor=kw.pop('vendor')
        elif kw['vendor_id'] and isinstance(kw['vendor'],int):
            self.vendor_id=kw.pop('vendor_id')
        else:
            raise ArgumentError('no vendor or vendor_id specified')
        if kw['name']:
            if isinstance(kw['name'],str):
                self.name = kw['name'].lower().strip()
        else:
            raise ArgumentError('no name provided for cpu')
        if kw['speed'] and isinstance(kw['speed'],int):
            self.speed=kw.pop('speed')
        else:
            try:
                self.speed = int(kw['speed'])
            except:
                raise ArgumentError('Speed must be an integer number')

mapper(Cpu,cpu,properties={
    'vendor'         : relation(Vendor),
    'creation_date' : deferred(cpu.c.creation_date),
    'comments'      : deferred(cpu.c.comments)
})

machine = Table('machine', meta,
    Column('id', Integer, Sequence('machine_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, nullable=False, index=True), #nodename
    Column('location_id', Integer, ForeignKey('location.id'), nullable=False),
    Column('model_id', Integer, ForeignKey('model.id'), nullable=False),
    Column('serial_no', String(64),nullable=True),
    Column('cpu_id', Integer, ForeignKey('cpu.id'), nullable=False), #DEFAULT ME
    Column('cpu_quantity', Integer, nullable=False, default=2), #CheckContstraint
    Column('memory', Integer, nullable=False, default=512), #IN MB. Default better
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
machine.create(checkfirst=True)

class Machine(aqdbBase):
    """ Represents any kind of computer that we need to model. This spans
        workstations, rackmount or chassis servers.
    """
    @optional_comments
    def __init__(self,*args,**kw):
        #loc was arg1
        if args[0]:
            loc = args[0]
            self.location = loc
        else:
            #TODO accept from kw location rack or chassis
            raise ArgumentError('No Location specified')
        if kw.has_key("serial_no"):
            self.serial_no = str(kw.pop("serial_no"))
        #model was arg2
        #self.model = model
        if args[1]:
            m=args[1]
        elif kw['model']:
            m=kw.pop('model')
        if isinstance(m,Model):
                self.model=m
                typ=m.machine_type
        elif isinstance(m,str):
            m=m.strip().lower()
            stmnt="select id from model where name = '%s'"%(m)
            m_id=engine.execute(stmnt).scalar()
            if not m_id:
                raise ArgumentError('cant find model %s'%m)
            else:
                self.model_id=m_id
        elif kw['model_id']:
            m_id=kw.pop('model_id')
            if isinstance(m_id,int):
                self.model_id=m_id
                assert(self.model_id)
        else:
            raise ArgumentError("No model supplied")

        #TODO: make name and node#/chassis loc mutually exclusive
        if kw.has_key('name'):
            self.name=kw.pop('name')
        #if loc = chassis then get a node #
        elif str(loc.type)=='chassis':
            if kw.has_key('node'):
                if isinstance(kw['node'],int):
                    self.name= ''.join([loc.name, 'n', str(kw.pop('node'))])
                else:
                    msg="'node' must be integer, '%s' is type '%s'"%(kw['node'],
                                                               type(kw['node']))
                    raise TypeError(msg.lstrip())
        #if loc = rack/its a rackmount, nodename is faked (how is TBD),
        #  create a new unique chassis for it with 1 slot.
        #if loc = desk: TBD, building for now
        #TODO: validate that this model type can go in this location type

        #Get data for creation of plenary hardware template
        MS=machine_specs.alias('MS')

        sl=select([MS.c.cpu_id,MS.c.cpu_quantity,MS.c.memory,MS.c.disk_type_id,
                   MS.c.disk_capacity,MS.c.nic_count],
            MS.c.model_id==self.model_id)

        #TODO: create a decorator for these...
        try:
            specs=engine.execute(sl).fetchone()
        except Exception,e:
            raise Exception(e)

#        from shell import ipshell
#        ipshell()
        #assert(specs)
        if specs:
            self.cpu_id       = specs['cpu_id']
            self.cpu_quantity = specs['cpu_quantity']
            self.memory          = specs['memory']
        if kw.has_key("cpu"):
            if isinstance(kw["cpu"],Cpu):
                self.cpu=kw.pop("cpu")
            else:
                msg='cpu argument should be a cpu object got '
                raise ArgumentError(msg + str(type(kw["cpu"])))
        if kw.has_key("cpu_quantity"):
            self.cpu_quantity = int(kw.pop("cpu_quantity"))
        if kw.has_key("memory"):
            self.memory = int(kw.pop("memory"))

        #TODO: we should probably let the caller get this althogether

    def __repr__(self):
        return 'Machine: %s is a %s located in %s'%(
            self.name,self.model,self.location)
    def type(self):
        return str(self.model.machine_type)

mapper(Machine,machine, properties={
    'location'      : relation(Location,uselist=False),
    'model'         : relation(Model,uselist=False),
    'cpu'           : relation(Cpu,uselist=False),
    'creation_date' : deferred(machine.c.creation_date),
    'comments'      : deferred(machine.c.comments)
})

disk=Table('disk',meta,
    Column('id', Integer, Sequence('disk_id_seq'), primary_key=True),
    #device name? (sda?) #boot? filesystem? this gets unweildy fast...
    Column('machine_id', Integer,
           ForeignKey('machine.id', ondelete='CASCADE'), nullable=False),
    Column('disk_type_id', Integer,
           ForeignKey('disk_type.id'), nullable=False),
    Column('capacity', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
disk.create(checkfirst=True)

class Disk(aqdbBase):
    """ join disk type with its capacity (GB) and what machine its in"""
    @optional_comments
    def __init__(self,**kw):
        if kw['machine']:
            if isinstance(kw['machine'],Machine):
                self.machine=kw.pop('machine')
            else:
                msg='machine argument should be a machine object'
                ' '.join([msg,'got %s'%(type(machine))])
                raise ArgumentError(msg)
        if kw['type']:
            if isinstance(kw['type'],DiskType):
                self.type=kw['type']
            elif isinstance(kw['type'],str):
                try:
                    type_id=engine.execute(
                        select([disk_type.c.id]).where(
                            disk_type.c.type==type)).scalar() #fetchone()[0]
                    assert(type_id)
                except Exception,e:
                    print e
                    raise ArgumentError("can't find disk_type '%s'"%type)
                self.disk_type_id=type_id
            else:
                raise ArgumentError('Disk type mist be DiskType or string type')
        try:
            self.capacity=int(kw.pop('capacity',0))
        except:
            raise ArgumentError('Capacity must be an integer number')

    def __repr__(self):
        return str(self.type)+" disk with %d capacity"%(self.capacity)

mapper(Disk,disk, properties={
    'machine'       : relation(Machine,backref='disks'),
    'type'          : relation(DiskType),
    'creation_date' : deferred(disk.c.creation_date),
    'comments'      : deferred(disk.c.comments)
})

machine_specs=Table('machine_specs', meta,
    Column('id', Integer, Sequence('mach_specs_id_seq'), primary_key=True),
    Column('model_id', Integer, ForeignKey('model.id'), nullable=False),
    Column('cpu_id', Integer, ForeignKey('cpu.id'), nullable=False),
    Column('cpu_quantity', Integer, nullable=False),
     #amount of RAM, specified in MB. AQ should take M or G args and convert
    Column('memory', Integer, nullable=False, default='512'),
    Column('disk_type_id', Integer, ForeignKey('disk_type.id'), nullable=False),
    Column('disk_capacity', Integer, nullable=False, default=36), #in GB
    #TODO: merge old nic code
    #Column('nic_driver', String(32), nullable=True),
    Column('nic_count', Integer, nullable=False, default=2),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
machine_specs.create(checkfirst=True)

class MachineSpecs(aqdbBase):
    """ Caputres the configuration hardware components for a given model """
    #TODO: single dict inside machine_type?
    #TODO: put disk capacity, type in here, make it consisitent
    _def_cpu_cnt={ 'workstation':1, 'blade': 2, 'rackmount' : 4 }
    _def_nic_cnt={ 'workstation':1, 'blade': 2, 'rackmount' : 2 }
    _def_memory ={ 'workstation': 2048, 'blade': 8192, 'rackmount': 16384 }

    @optional_comments
    def __init__(self,**kw):
        #TODO: fix this hackish ugly stuff
        typ=None #temporary var
        print "MODEL"
        if kw['model']:
            m=kw.pop('model')
            if isinstance(m,Model):
                self.model=m
                typ=m.machine_type.type
            elif isinstance(m,str):
                m=m.strip().lower()
                stmnt="select id from model where name = '%s'"%(m)
                m_id=engine.execute(stmnt).scalar()
                if not m_id:
                    raise ArgumentError('cant find model %s'%m)
                else:
                    self.model_id=m_id
        elif kw['model_id']:
            m_id=kw.pop('model_id')
            if isinstance(m_id,int):
                self.model_id=m_id
        else:
            raise ArgumentError("No model supplied")

        if not typ:
            assert(self.model_id)
            stmt= """select type from machine_type where id = (select
                machine_type_id from model where id = %s)"""%(self.model_id)
            typ=engine.execute(stmt).scalar()
            assert(typ)
        print "CPU"
        if kw['cpu']:
            m=kw.pop('cpu')
            if isinstance(m,Model):
                self.cpu=m
            elif isinstance(m,str):
                m=m.strip().lower()
                stmnt="select id from cpu where name = '%s'"%(m)
                m_id=engine.execute(stmnt).scalar()
                assert(m_id)
                self.cpu_id=m_id
        elif kw['cpu_id']:
            m_id=kw.pop('cpu_id')
            if isinstance(m_id,int):
                self.cpu_id=m_id
        else:
            raise ArgumentError("No cpu supplied")

        cc=kw.pop('cpu_quantity',None)
        if cc:
            try:
                self.cpu_quantity=int(cc)
            except:
                raise ArgumentError('CPU count should be a positive integer number')
            if self.cpu_quantity < 1:
                raise ArgumentError('CPU count should be a positive integer number')
        else:
            assert(typ)
            self.cpu_quantity=MachineSpecs._def_cpu_cnt[typ]
        #TODO: remove default scsi type.
        stmt="select id from disk_type where type = '%s'"%(kw.pop(
            'disk_type','scsi'))
        self.disk_type_id=engine.execute(stmt).scalar()
        assert(self.disk_type_id)
        print "MEM", typ
        self.memory=int(kw.pop('memory', MachineSpecs._def_memory[typ]))
        print "DISK"
        self.disk_capacity=int(kw.pop('disk_capacity','36'))
        print "NIC"
        self.nic_count=kw.pop('nic_count',MachineSpecs._def_nic_cnt[typ])


mapper(MachineSpecs,machine_specs, properties={
    'model'         : relation(Model,backref='specsifcations'),
    'cpu'           : relation(Cpu),
    'creation_date' : deferred(machine_specs.c.creation_date),
    'comments'      : deferred(machine_specs.c.comments)})

####POPULATION ROUTINES####
def populate_vendor():
    if empty(vendor):
        print "Populating vendor"
        import configuration as cfg
        from aquilon import const
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
        #hack alert:
        b=Vendor('hp')
        Session.save(b)
        try:
            Session.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            Session.close()

def populate_machine_type():
    if empty(machine_type):
        print "Populating machine_type"
        fill_type_table(machine_type,['rackmount',
                                       'blade', 'workstation','nic'])
def populate_disk_type():
    if empty(disk_type):
        print 'Populating disk_types... ',
        import configuration as cfg
        from aquilon import const
        d=os.path.join(const.cfg_base,'hardware/harddisk/generic')
        disk_types=[]
        for i in os.listdir(d):
            disk_types.append(os.path.splitext(i)[0])
        fill_type_table(disk_type,disk_types)
        print '%s'%(disk_types)

def populate_machines():
    s = Session()
    mlist=s.query(Model).all()

    if not mlist:
        print "Populating model table"

        v_cache = gen_id_cache(Vendor)

        hwt_cache={}
        for c in s.query(MachineType).all():
            hwt_cache[str(c)] = c
        print hwt_cache

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

def populate_cpu():
    if empty(cpu):
        print "Populating cpus"
        import re
        m=re.compile('speed')

        import configuration as cfg
        from aquilon import const
        #get all dir names immediately under template-king/hardware/cpu/
        base=os.path.join(str(const.cfg_base),'hardware/cpu')
        cpus=[]
        for i in os.listdir(base):
            for j in os.listdir(os.path.join(base,i)):
                name = j.rstrip('.tpl').strip()
                with open(os.path.join(base,i,j),'r') as f:
                    assert(m)
                    for line in f.readlines():
                        a_match=m.search(line)
                        if a_match:
                            l,e,freq=line.partition('=')
                            assert(isinstance(freq,str))
                            speed=re.sub('\*MHz','',freq.strip().rstrip(';'))
                            #TODO: better checking if freq is ok here
                            if speed.isdigit():
                                cpus.append([i,name,speed])
                                break
                            else:
                                Assert(False)
                    f.close()

        for vendor,name,speed in cpus:
            kw={}
            vendor=Session.query(Vendor).filter_by(name=vendor).first()
            assert(vendor)
            assert(name)
            assert(speed)
            if vendor:
                kw['vendor'] = vendor
                kw['name']   = name
                kw['speed']  = int(speed)
                a=Cpu(**kw)
                assert(isinstance(a,Cpu))
                try:
                    Session.save(a)
                except Exception,e:
                    Session.rollback()
                    print e
                    continue
            else:
                msg="CREATE CPU: cant find vendor '%s'"%(vendor)
                if logging:
                    logging.error(msg)
                else:
                    print >> sys.stderr, msg
        try:
            Session.commit()
        except Exception,e:
            Session.rollback()
            print e
        print 'Created cpus'

def populate_status():
    if empty(status):
        i=status.insert()
        for name in ['prod','dev','qa','build']:
            i.execute(name=name)


def populate_m_configs():
    if empty(machine_specs):
        a=MachineSpecs(model='hs20',cpu='xeon_2660',comments='FAKE')
        b=MachineSpecs(model='hs21',cpu='xeon_2660',
                                disk_capacity=68, comments='FAKE')
        c=MachineSpecs(model='poweredge_6650', cpu='xeon_3000',cpu_quantity=4,
                                comments='FAKE')
        d=MachineSpecs(model='bl45p',cpu='opteron_2600',memory=32768,
                                comments='FAKE')
        for ms in [a,b,c,d]:
            try:
                Session.save(ms)
            except Exception,e:
                Session.rollback()
                print 'Saving:', e
                continue
            try:
                Session.commit()
            except Exception,e:
                Session.rollback()
                print 'Commiting ',e
                continue


if __name__ == '__main__':
    populate_status()
    populate_vendor()
    populate_machine_type()
    populate_machines()
    populate_disk_type()
    populate_cpu()
    populate_m_configs()
#TODO:
#   check if it exists in dbdb minfo, and get from there if it does
#   and/or -dsdb option, and, make machine --like [other machine] + overrides
