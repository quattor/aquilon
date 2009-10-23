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
""" For Systems and related objects """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, Host,  ServiceInstance, CfgPath

#TODO: auto-updated "last_used" column?
#TODO: uselist=False for host, lazy=False for service_instance?
class BuildItem(Base):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    __tablename__ = 'build_item'

    id = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id = Column('host_id', Integer, ForeignKey('host.id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                      nullable=False)

    cfg_path_id = Column(Integer, ForeignKey(
        'cfg_path.id', name='build_item_cfg_path_fk'), nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    # Having lazy=False here is essential.  This outer join saves
    # thousands of queries whenever finding clients of a service
    # instance.
    host = relation(Host, backref='build_items', lazy=False)
    service_instance = relation(ServiceInstance, uselist=False)
    cfg_path = relation(CfgPath, uselist=False, backref='build_items')


    def __repr__(self):
        return '%s: %s'%(self.host.name,self.service_instance.cfg_path)

build_item = BuildItem.__table__

build_item.primary_key.name='build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'service_instance_id', name='build_item_uk'))

Host.templates = relation(BuildItem,
                         collection_class=ordering_list('position'),
                         order_by=['build_item.position'])

table = build_item
