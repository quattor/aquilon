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
from datetime import datetime
import sys
sys.path.insert(0, '..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

import depends
from sqlalchemy import (UniqueConstraint, Table, Column, Integer, DateTime,
                        Sequence, String, select, ForeignKey, Index)

from sqlalchemy.orm import mapper, relation, deferred, backref
from sqlalchemy.sql.expression import alias

from db import Base, aqdbBase, optional_comments
from subtypes import subtype, get_subtype_id, populate_subtype
from aquilon.exceptions_ import ArgumentError

from cpu import Cpu, cpu
from model import vendor, Model, model
from disk_type import DiskType, disk_type
from configuration import CfgPath, cfg_path
from machine_specs import MachineSpecs, machine_specs
from location import Location, location, Chassis, chassis

class Machine(Base):
    __tablename__ = 'machine'
    id = Column(Integer, Sequence('machine_id_seq'), primary_key=True)
    name = Column('name', String(32), nullable=False, index=True)

    location_id = Column(Integer,
                         ForeignKey('location.id', name ='machine_loc_fk'),
                         nullable = False)

    model_id = Column(Integer,
                      ForeignKey('model.id', name = 'machine_model_fk'),
                      nullable = False)

    cpu_id = Column(Integer,
                    ForeignKey('cpu.id', name = 'machine_cpu_fk'),
                    nullable = False) #TODO: default somehow...

    cpu_quantity = Column(Integer, nullable=False, default=2) #TODO: constrain
    memory = Column(Integer, nullable=False, default=512) #TODO: beter default?
    serial_no = Column(String(64),nullable=True)
    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, uselist=False)
    model    = relation(Model, uselist=False)
    cpu      = relation(Cpu, uselist=False)
#add unique constraint to name
machine = Machine.__table__
machine.primary_key.name = 'machine_pk'
machine.append_constraint(
    UniqueConstraint('name',name = 'machine_name_uk')
)

Index('machine_name_ix', machine.c.name)
Index('machine_loc_ix', machine.c.location_id)

#machine = Table('machine', Base.metadata,
#    Column('id', Integer, Sequence('machine_id_seq'), primary_key=True),
#    Column('name', String(32), unique=True, nullable=False, index=True), #nodename
#    Column('location_id', Integer, ForeignKey('location.id'), nullable=False),
#    Column('model_id', Integer, ForeignKey('model.id'), nullable=False),
#    Column('serial_no', String(64),nullable=True),
#    Column('cpu_id', Integer, ForeignKey('cpu.id'), nullable=False), #DEFAULT ME
#    Column('cpu_quantity', Integer, nullable=False, default=2), #CheckContstraint
#    Column('memory', Integer, nullable=False, default=512), #IN MB. Default better
#    Column('creation_date', DateTime, default=datetime.now),
#    Column('comments', String(255), nullable=True))
#
#class Machine(aqdbBase):
#    """ Represents any kind of computer that we need to model. This spans
#        workstations, rackmount or chassis servers.
#    """
#    @optional_comments
#    def __init__(self,*args,**kw):
#        #loc was arg1
#        if args[0]:
#            loc = args[0]
#            self.location = loc
#        else:
#            #TODO accept from kw location rack or chassis
#            raise ArgumentError('No Location specified')
#        if kw.has_key("serial_no"):
#            self.serial_no = str(kw.pop("serial_no"))
#        #model was arg2
#        #self.model = model
#        if args[1]:
#            m=args[1]
#        elif kw['model']:
#            m=kw.pop('model')
#        if isinstance(m,Model):
#                self.model=m
#                typ=m.machine_type
#        elif isinstance(m,str):
#            m=m.strip().lower()
#            stmnt="select id from model where name = '%s'"%(m)
#            m_id=engine.execute(stmnt).scalar()
#            if not m_id:
#                raise ArgumentError('cant find model %s'%m)
#            else:
#                self.model_id=m_id
#        elif kw['model_id']:
#            m_id=kw.pop('model_id')
#            if isinstance(m_id,int):
#                self.model_id=m_id
#                assert(self.model_id)
#        else:
#            raise ArgumentError("No model supplied")
#
#        #TODO: make name and node#/chassis loc mutually exclusive
#        if kw.has_key('name'):
#            self.name=kw.pop('name')
#        #if loc = chassis then get a node #
#        elif str(loc.type)=='chassis':
#            if kw.has_key('node'):
#                if isinstance(kw['node'],int):
#                    self.name= ''.join([loc.name, 'n', str(kw.pop('node'))])
#                else:
#                    msg="'node' must be integer, '%s' is type '%s'"%(kw['node'],
#                                                               type(kw['node']))
#                    raise TypeError(msg.lstrip())
#        #if loc = rack/its a rackmount, nodename is faked (how is TBD),
#        #  create a new unique chassis for it with 1 slot.
#        #if loc = desk: TBD, building for now
#        #TODO: validate that this model type can go in this location type
#
#        #Get data for creation of plenary hardware template
#        MS=machine_specs.alias('MS')
#
#        sl=select([MS.c.cpu_id,MS.c.cpu_quantity,MS.c.memory,MS.c.disk_type_id,
#                   MS.c.disk_capacity,MS.c.nic_count],
#            MS.c.model_id==self.model_id)
#
#        #TODO: create a decorator for these...
#        try:
#            specs=engine.execute(sl).fetchone()
#        except Exception,e:
#            raise Exception(e)
#
#        if specs:
#            self.cpu_id       = specs['cpu_id']
#            self.cpu_quantity = specs['cpu_quantity']
#            self.memory          = specs['memory']
#        if kw.has_key("cpu"):
#            if isinstance(kw["cpu"],Cpu):
#                self.cpu=kw.pop("cpu")
#            else:
#                msg='cpu argument should be a cpu object got '
#                raise ArgumentError(msg + str(type(kw["cpu"])))
#        if kw.has_key("cpu_quantity"):
#            self.cpu_quantity = int(kw.pop("cpu_quantity"))
#        if kw.has_key("memory"):
#            self.memory = int(kw.pop("memory"))
#
#        #TODO: we should probably let the caller get this althogether
#
#    def __repr__(self):
#        return 'Machine: %s is a %s located in %s'%(
#            self.name,self.model,self.location)
#    def type(self):
#        return str(self.model.machine_type)
#
#mapper(Machine,machine, properties={
#    'location'      : relation(Location, uselist=False),
#    'model'         : relation(Model, uselist=False),
#    'cpu'           : relation(Cpu, uselist=False),
#    'creation_date' : deferred(machine.c.creation_date),
#    'comments'      : deferred(machine.c.comments)
#})


#TODO:
#   check if it exists in dbdb minfo, and get from there if it does
#   and/or -dsdb option, and, make machine --like [other machine] + overrides
