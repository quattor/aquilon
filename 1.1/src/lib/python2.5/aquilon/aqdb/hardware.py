#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

#import datetime

from sys import path,exit
#path.append('./utils')

from aquilon.aqdb.DB import meta, engine, Session, aqdbBase
from aquilon.aqdb.utils.debug import ipshell
from aquilon.aqdb.utils.schemahelpers import *

from sqlalchemy import *
from sqlalchemy.orm import *

#TODO: add sequences to everything

vendor = mk_name_id_table('vendor',meta)

class Vendor(object):
    '''wraps rows of the vendor table
        CHILD OF: model '''
    def __init__(self,name,**kw):
        self.name = name.lower().strip()
    def __repr__(self):
        return str(self.name)
mapper(Vendor,vendor)

################ TYPE ############
hardware_type = mk_name_id_table('hardware_type', meta)
class HardwareType(aqdbBase):
    def __init__(self,name):
        self.name=name.lower().strip()
    def __repr__(self):
        return str(self.name)
mapper(HardwareType,hardware_type)
#'blade', 'rackmount', 'workstation'

model = Table('model',meta,
    Column('id', Integer, primary_key=True, index=True),
    Column('name', String(64), unique=True, nullable=False, index=True),
    Column('vendor_id', Integer,
           ForeignKey('vendor.id', ondelete='RESTRICT'), nullable=False),
    #cpu: template pointer
    #cpu count
    #ram: template pointer
    #ram amount integer (in MB?)
    Column('comments',String(255)))

class Model(aqdbBase):
    '''wraps rows in model.
           PARENT OF: vendor
    '''
    @optional_comments
    def __init__(self,name,vendor,**kw):
        self.name = name.lower().strip()
        #TODO: more friendly error msg than KeyError:i.e. type check input
        self.hardware_type = kw.pop('hardware_type')
        if isinstance(vendor,Vendor):
            self.vendor = vendor
        else:
            v=Vendor(vendor)
            s.save(v)
            self.vendor=v
            s.flush()


    def __repr__(self):
        return '%s %s'%(self.vendor,self.name)

mapper(Model,model,properties={
    'vendor': relation(Vendor,backref='model'),
    'hardware_type': relation(HardwareType,backref='model')
})

#template name, key, and value

hardware = Table('hardware',meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), unique=True, index=True),
    Column('location_id', Integer,
           ForeignKey('location.id'), index=True),
    Column('type_id', Integer,
           ForeignKey('hardware_type.id',ondelete='RESTRICT')),
    Column('cfg_path_id',Integer,
            ForeignKey('cfg_path.id',ondelete='RESTRICT'),
            unique=True),
    Column('serialnumber', String(64), unique=True, nullable=True),
    Column('comments', String(255)))

rackmount = Table('rackmount', meta,
    Column('id',Integer,ForeignKey('hardware.id'), primary_key=True))

blade = Table('blade', meta,
    Column('id', Integer, ForeignKey('hardware.id'), primary_key=True))

workstation = Table('workstation', meta,
    Column('id',Integer, ForeignKey('hardware.id'), primary_key=True))
    #user/owner?

interface_type=mk_name_id_table('interface_type')
#physical, zebra, service, heartbeat, Router,management, ipmi, vlan, build

interface = Table('interface',meta,
    Column('id', Integer, primary_key=True),
    Column('interface_type_id', Integer,
           ForeignKey('interface_type.id'), nullable=False),
    Column('ip',String(16), default='0.0.0.0', index=True)) #TODO FK to IP table)

physical_interface=Table('physical_interface', meta,
    Column('interface_id', Integer,
           ForeignKey('interface.id'),primary_key=True),
    Column('hardware_id', Integer,
           ForeignKey('hardware.id',ondelete='CASCADE'),
           nullable=False, index=True),
    Column('name',String(255), nullable=False), #like e0, hme1, etc.
    Column('mac', String(32), nullable=False, unique=True, index=True),
    UniqueConstraint('hardware_id','name'))

"""
    need disk table. type comes from cfg_path
"""

#"/hardware" = create("machine/na/np/6/31_c5n12");
"""
structure template machine/na/np/6/31_c5n9;

"location" = "np.ny.na";
"serialnumber" = "99C5549";

# This is a ibm bladecenter hs21
include hardware/models/ibm_hs21;

"ram" = list(create("hardware/ram/generic", "size", 8192*MB));
"cpu" = list(create("hardware/cpu/intel_xeon_2660"),
             create("hardware/cpu/intel_xeon_2660"));
"harddisks" = nlist("sda", create("hardware/harddisk/scsi", "capacity", 34*GB));

"cards/nic/eth0/hwaddr" = "00:14:5E:D7:9A:E4";
"cards/nic/eth0/boot" = true;
"cards/nic/eth1/hwaddr" = "00:14:5E:D7:9A:E6";
"""
#""" path to template is assumed as /hardware/vendor/model """
#hardware_cfg_path = Table('hardware_cfg_path',meta,
#    Column('id', Integer, ForeignKey('cfg_path.id'), primary_key=True),
#    Column('model_id', Integer,
#        ForeignKey('model.id', ondelete='RESTRICT'), nullable=False))
