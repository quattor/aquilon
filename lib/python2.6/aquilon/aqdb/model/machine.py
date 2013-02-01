# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""The tables/objects/mappings related to hardware in Aquilon. """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm  import relation

from aquilon.aqdb.model import Cpu, HardwareEntity


class Machine(HardwareEntity):
    """ Machines represents general purpose computers """

    __tablename__ = 'machine'
    __mapper_args__ = {'polymorphic_identity': 'machine'}

    #TODO: should this be named hardware_entity_id?
    machine_id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name='machine_hw_ent_fk',
                                           ondelete='CASCADE'),
                                           primary_key=True)

    cpu_id = Column(Integer, ForeignKey(
        'cpu.id', name='machine_cpu_fk'), nullable=False)

    #TODO: constrain/smallint
    cpu_quantity = Column(Integer, nullable=False, default=2)

    memory = Column(Integer, nullable=False, default=512)

    cpu = relation(Cpu)

    @property
    def cluster(self):
        if self.vm_container and hasattr(self.vm_container.holder, 'cluster'):
            return self.vm_container.holder.holder_object
        else:
            return None


machine = Machine.__table__  # pylint: disable=C0103
machine.primary_key.name = 'machine_pk'


#TODO: an __init__ (or other method) that could use DSDB to create itself?
#   check if it exists in dbdb minfo, and get from there if it does
#    and/or -dsdb option, and, make machine --like [other machine] + overrides

#TODO: an __init__ that uses the machine specs to dynamically populate default
#      values for all of the attrs where its possible
