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
""" Connection from any hardware entity to a serial_cnxn """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, ForeignKey, Sequence,
                             UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, ConsoleServer, HardwareEntity
from aquilon.aqdb.column_types.aqstr import AqStr

class SerialCnxn(Base):
    """ serial connection: harware_ent/name/cons_svr/port# table. """

    __tablename__ = 'serial_cnxn'

    id = Column(Integer, Sequence(name='serial_cnxn_seq'), primary_key=True)

    console_server_id = Column(Integer, ForeignKey('console_server.id',
                                                   name='serial_cnxn_cons_svr_fk',
                                                   ondelete='CASCADE'),
                               nullable=False)

    port_number = Column(Integer, nullable=False )

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='serial_cnxn_hw_ent_fk',
                                                    ondelete='CASCADE'),
                                nullable=False)

    name = Column(AqStr(64), nullable=False)

serial_cnxn = SerialCnxn.__table__
serial_cnxn.primary_key.name='serial_cnxn_pk'

serial_cnxn.append_constraint(UniqueConstraint(
    'console_server_id','port_number', name='serial_cnxn_cons_port_uk'))

serial_cnxn.append_constraint(UniqueConstraint(
    'hardware_entity_id', 'name', name='serial_cnxn_hw_name_uk'))

table = SerialCnxn.__table__


