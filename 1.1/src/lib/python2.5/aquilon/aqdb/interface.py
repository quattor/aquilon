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
import re
import datetime

from db import *
from aquilon import const

from sqlalchemy import Table, DateTime, Boolean, UniqueConstraint, Index
from sqlalchemy.orm.collections import attribute_mapped_collection

from location import Location,Chassis
from hardware import Machine
from aquilon.exceptions_ import ArgumentError


location=Table('location', meta, autoload=True)
chassis=Table('chassis', meta, autoload=True)
cfg_path=Table('cfg_path', meta, autoload=True)
machine=Table('machine', meta, autoload=True)

from sqlalchemy import Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

interface_type=mk_type_table('interface_type',meta)
interface_type.create(checkfirst=True)

class InterfaceType(aqdbType):
    """ AQDB will support different types of interfaces besides just the usual
        physical type. Other kinds in the environment include zebra, service,
        heartbeat, router, mgmt/ipmi, vlan/802.1q, build. At the moment we;re
        only implementing physical, with zebra and 802.1Q likely to be next"""
    pass

mapper(InterfaceType, interface_type, properties={
    'creation_date':deferred(interface_type.c.creation_date),
    'comments': deferred(interface_type.c.comments)})
if empty(interface_type):
    fill_type_table(interface_type,['physical','zebra','service','802.1q',
            'base_interface_type'])

interface = Table('interface',meta,
    Column('id', Integer, Sequence('interface_id_seq'), primary_key=True),
    Column('interface_type_id', Integer,
           ForeignKey('interface_type.id'), nullable=False),
    Column('ip',String(16), default='0.0.0.0', index=True),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments',String(255))) #TODO FK to IP table)
interface.create(checkfirst=True)

class Interface(aqdbBase):
    """ Base Class of various network interface structures """
    def __init__(self, name, *args,**kw):
        self.name = name.strip().lower()
        if (kw.has_key('ip')):
            self.ip = kw['ip']
        else:
            self.ip = ''

mapper(Interface,interface,
       polymorphic_on=interface.c.interface_type_id,
        polymorphic_identity=engine.execute(
           "select id from interface_type where type='base_interface_type'").\
            fetchone()[0], properties={
                        'type': relation(InterfaceType),
                        'creation_date' : deferred(interface.c.creation_date),
                        'comments': deferred(interface.c.comments)})

physical_interface=Table('physical_interface', meta,
    Column('interface_id', Integer,
           ForeignKey('interface.id', ondelete='CASCADE'), primary_key=True),
    Column('machine_id', Integer,
           ForeignKey('machine.id',ondelete='CASCADE'),
           nullable=False),
    Column('name',String(32), nullable=False), #like e0, hme1, etc.
    Column('mac', String(32), nullable=False),
    Column('boot', Boolean, default=False),
    #creation/comments supplied by Super (Interface)
    UniqueConstraint('mac',name='mac_addr_uk'),
    UniqueConstraint('machine_id','name',name='phy_iface_uk'))
Index('idx_phys_int_machine_id', physical_interface.c.machine_id)
physical_interface.create(checkfirst=True)

class PhysicalInterface(Interface):
    """ Class to model up the physical nic cards/devices in machines """
    @optional_comments
    def __init__(self, name, mac, machine, *args,**kw):
        Interface.__init__(self, name, *args, **kw)
        self.name = name.strip().lower()
        self.mac  = mac.strip().lower()
        reg = re.compile('^([a-f0-9]{2,2}:){5,5}[a-f0-9]{2,2}$')
        if (not reg.match(self.mac)):
            raise ArgumentError ('Invalid MAC address: '+self.mac)
        self.machine= machine
        if kw.has_key('boot'):
            self.boot=kw.pop('boot')
        elif self.name == 'e0':
            self.boot=True
        #TODO: tighten this up with type/value checks
        #we should probably also constrain the name

mapper(PhysicalInterface, physical_interface,
       inherits=Interface, polymorphic_identity=engine.execute(
           "select id from interface_type where type='physical'").\
            fetchone()[0], properties={
    'machine':      relation(Machine,backref='interfaces'),
    'interface':    relation(Interface,lazy=False,backref='physical')})
    #collection_clas=attribute_mapped_collection('name'))})


def populate_physical():
    if empty(physical_interface):
        m=Session.query(Machine).first()
        try:
            pi=PhysicalInterface('e0','00:ae:0f:11:bb:cc',m)
        except Exception,e:
            print e

        Session.save(pi)
        Session.commit()

#if __name__ == '__main__':
