# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Machine Specifications: the rows of this table represent the default
    values of machine "models" so that users don't need to manaully enter the
    low level details of each one since this is mostly repeated data in large
    grid deployments, such as Saphire """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Model, Vendor, Cpu, DiskType


class MachineSpecs(Base):
    """ Captures the configuration hardware components for a given model """
    #TODO: Maybe this entire table is in fact a part of the model "subtype"

    _def_cpu_cnt = { 'workstation':1, 'blade': 2, 'rackmount' : 4 }
    _def_nic_cnt = { 'workstation':1, 'blade': 2, 'rackmount' : 2 }
    _def_memory  = { 'workstation': 2048, 'blade': 8192, 'rackmount': 16384 }

    __tablename__ = 'machine_specs'
    id = Column( Integer, Sequence('mach_specs_id_seq'), primary_key=True)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='mach_spec_model_fk'),
                      nullable=False)

    cpu_id = Column(Integer, ForeignKey('cpu.id', name='mach_spec_cpu_fk'), nullable=False)

    cpu_quantity = Column(Integer, nullable=False) #Constrain to below 512?

    memory = Column(Integer, nullable=False, default=0)
    disk_type_id = Column(Integer, ForeignKey('disk_type.id',
                                              name='mach_spec_disk_typ_fk'),
                           nullable=False)

    disk_capacity = Column(Integer, nullable=False, default=36)
    nic_count = Column(Integer, nullable=False, default=2)

    creation_date = deferred(Column('creation_date', DateTime, default=datetime.now))
    comments = deferred(Column('comments', String(255), nullable=True))

    model = relation(Model, backref=backref('machine_specs', uselist=False))
    cpu = relation(Cpu)
    disk_type = relation(DiskType)


machine_specs = MachineSpecs.__table__

machine_specs.primary_key.name='machine_specs_pk'
#for now, need a UK on model_id. WILL be a name AND a model_id as UK.
machine_specs.append_constraint(
    UniqueConstraint('model_id', name='machine_spec_model_id_uk'))

table = machine_specs

def populate(sess, *args, **kw):
    if len(sess.query(MachineSpecs).all()) < 1:
        from sqlalchemy import insert

        specs = [["hs20-884345u", "xeon_2660", 2, 8192, 'scsi', 36, 2],
             ["hs21-8853l5u", "xeon_2660", 2, 8192, 'scsi', 68, 2],
             ["poweredge_6650", "xeon_3000", 4, 16384, 'scsi', 36, 2],
             ["bl45p", "opteron_2600", 2, 32768, 'scsi', 36, 2],
             ["bl260c", "xeon_2500", 2, 24576, 'scsi', 36, 2],
             ["vb1205xm", "xeon_2500", 2, 24576, 'scsi', 36, 2],
             ["aurora_model", "aurora_cpu", 0, 0, 'scsi', 0, 0]]


        for ms in specs:
            try:
                dbmodel = sess.query(Model).filter_by(name=ms[0]).one()
                dbcpu = sess.query(Cpu).filter_by(name=ms[1]).one()
                cpu_quantity = ms[2]
                memory = ms[3]
                dbdisk_type = sess.query(DiskType).filter_by(type=ms[4]).one()
                disk_capacity = ms[5]
                nic_count = ms[6]
                dbms = MachineSpecs(model=dbmodel, cpu=dbcpu,
                        cpu_quantity=cpu_quantity, memory=memory,
                        disk_type=dbdisk_type, disk_capacity=disk_capacity,
                        nic_count=nic_count)
                sess.add(dbms)
            except Exception,e:
                sess.rollback()
                print 'Creating machine specs: %s' % e
                continue
            try:
                sess.commit()
            except Exception,e:
                sess.rollback()
                print 'Commiting ',e
                continue
