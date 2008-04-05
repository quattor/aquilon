#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Classes and Tables relating to network interfaces"""
from __future__ import with_statement

import sys
sys.path.append('../..')

import os
import datetime

from db import *
from aquilon import const

from sqlalchemy import Table, DateTime, Boolean, UniqueConstraint

from location import Location,Chassis
from configuration import CfgPath
from hardware import Machine
import configuration #for cfg_base

location=Table('location', meta, autoload=True)
chassis=Table('chassis', meta, autoload=True)
cfg_path=Table('cfg_path', meta, autoload=True)
machine=Table('machine', meta, autoload=True)

from sqlalchemy import Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

const.nic_prefix ='hardware/nic/'
const.nic_directory=os.path.join(configuration.const.cfg_base,const.nic_prefix)
const.nics = os.listdir(const.nic_directory)

interface_type=mk_type_table('interface_type',meta)
interface_type.create(checkfirst=True)

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

class InterfaceType(aqdbType):
    """ AQDB will support different types of interfaces besides just the usual
        physical type. Other kinds in the environment include zebra, service,
        heartbeat, router, mgmt/ipmi, vlan/802.1q, build. At the moment we;re
        only implementing physical, with zebra and 802.1Q likely to be next"""
    pass

mapper(InterfaceType, interface_type, properties={
    'creation_date':deferred(interface_type.c.creation_date),
    'comments': deferred(interface_type.c.comments)})
if empty(interface_type,engine):
    fill_type_table(interface_type,['physical','zebra','service','802.1q',
            'base_interface_type'])

interface = Table('interface',meta,
    Column('id', Integer, Sequence('interface_id_seq'), primary_key=True),
    Column('interface_type_id', Integer,
           ForeignKey('interface_type.id'), nullable=False),
    Column('ip',String(16), default='0.0.0.0', index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255))) #TODO FK to IP table)
interface.create(checkfirst=True)

class Interface(aqdbBase):
    """ Base Class of various network interface structures """
    def __init__(self, name, *args,**kw):
        self.name = name.strip().lower()

mapper(Interface,interface,
       polymorphic_on=interface.c.interface_type_id,
        polymorphic_identity=Session.execute(
           "select id from interface_type where type='base_interface_type'").\
            fetchone()[0], properties={
                        'type': relation(InterfaceType),
                        'creation_date' : deferred(interface.c.creation_date),
                        'comments': deferred(interface.c.comments)})


nic = Table('nic', meta,
    Column('id', Integer, Sequence('nic_id_seq'), primary_key=True),
    Column('driver', String(16), unique=True, index=True),
    Column('name', String(64), unique=True),
    Column('pxe', Boolean, default=True),
    Column('cfg_path_id', Integer, ForeignKey('cfg_path.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
nic.create(checkfirst=True)

""" TODO:QWG tmeplate struct includes a driverrpms optional field...
        will we need a driver rpms table?
        (it would be a many to one of strings, against nic as parent)
"""
class Nic(aqdbBase):
    """ This table/class models the quattor/hardware/nic/* for host creation """
    @optional_comments
    def __init__(self,*args,**kw):
        msg = 'The Nic class is query only and cannot be instanced'
        raise ArgumentError(msg)
        return
    def __repr__(self):
        return str(self.name)
    def media(self):
        """ This is something of a hack but since it's the only value in use
            we'll go with it for now. """
        return 'ethernet'

mapper(Nic,nic, properties={
    'cfg_path': relation(CfgPath, backref='nic'),
    'creation_date' : deferred(nic.c.creation_date),
    'comments': deferred(nic.c.comments)
})

class NicTemplate(object):
    """ Helper object to read and write template files for nic structures """
    #TODO: subclass of Nic, or of a larger hardware template parser
    def __init__(self, **kw):
        if kw.has_key('file'):
            self.file = kw.pop('file')
            self.info=parse_template(self.file)

        elif kw.has_key('driver'):
            self.driver = driver

        if not self.file and not self.driver:
            msg = 'NicTemplate requires a file or driver argument'
            raise AttributeError(msg)

    def to_db(self):
        cfp = CfgPath('/'.join([const.nic_prefix,self.file]))
        Session.save(cfp)
        try:
            Session.commit()
        except Exception,e:
            print e
            Session.rollback()
            return
        self.info['cfg_path_id']=cfp.id
        del self.info['cfg_path']
        i = nic.insert()
        i.execute(**self.info)
        """ Now we have:
            n=Session.query(Nic).first()
            In [5]: n.cfg_path
            Out[5]: hardware/nic/3c59x.tpl

            TODO: to_file method which reads and interprets the data from the
            table, and writes it out as a file somewhere.
        """


physical_interface=Table('physical_interface', meta,
    Column('interface_id', Integer,
           ForeignKey('interface.id'), primary_key=True),
    Column('machine_id', Integer,
           ForeignKey('machine.id',ondelete='CASCADE'),
           nullable=False, index=True),
    Column('name',String(32), nullable=False), #like e0, hme1, etc.
    Column('nic_id', Integer, ForeignKey('nic.id'), nullable=False),
    Column('mac', String(32), nullable=False, unique=True, index=True),
    Column('boot', Boolean, default=False),
    #creation/comments supplied by Super (Interface)
    UniqueConstraint('machine_id','name'))
physical_interface.create(checkfirst=True)

class PhysicalInterface(Interface):
    """ Class to model up the physical nic cards/devices in machines """
    @optional_comments
    def __init__(self, name, nic, mac, machine, *args,**kw):
        self.name = name.strip().lower()
        self.mac  = mac.strip().lower()
        self.nic  = nic
        self.machine= machine
        if kw.has_key('boot'):
            self.boot=kw.pop('boot')
        elif self.name == 'e0':
            self.boot=True
        #TODO: tighten this up with type/value checks
        #we should probably also constrain the name

mapper(PhysicalInterface, physical_interface,
       inherits=Interface, polymorphic_identity=Session.execute(
           "select id from interface_type where type='physical'").\
            fetchone()[0], properties={
    'machine':      relation(Machine,backref='interfaces'),
    'nic':          relation(Nic),
    'interface':    relation(Interface,backref='physical')
})

def populate_nics():
    if empty(nic,engine):
        for n in const.nics:
            a=NicTemplate(file=n)
            a.to_db()
        print 'created nics %s'%(const.nics)

def populate_physical():
    if empty(physical_interface,engine):
        m=Session.query(Machine).first()
        nick=Session.query(Nic).filter_by(driver='tg3').one()
        try:
            pi=PhysicalInterface('e0',nick,'00:ae:0f:11:bb:cc',m)
        except Exception,e:
            print e

        Session.save(pi)
        Session.commit()

if __name__ == '__main__':
    populate_nics()
    #populate_physical()
