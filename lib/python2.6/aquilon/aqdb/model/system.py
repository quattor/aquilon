# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Systems are higher level constructs which can provide services """
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.sql import and_

from aquilon.exceptions_ import InternalError, ArgumentError
from aquilon.aqdb.model import Base, DnsDomain, Network
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr, IPV4

#TODO: enum type for system_type column
#_sys_types = ['host', 'switch', 'console_switch', 'chassis', 'manager',
#              'auxiliary' ]

class System(Base):
    """ System: a base class which abstracts out the details of between
        all the various kinds of service providers we may use. A System might be
        a host/server/workstation, router, firewall, netapp, etc. Naming this
        is kind of difficult, but "system" seems neutral, and happens not to
        be overloaded by anything I am aware of.

        This is exactly what system does. System_id holds a name, and presents
        an abstract entity that can provide, or utilize services, hardware,
        networks, configuration sources, etc. It's subtyped for flexibilty to
        weather future expansion and enhancement without breaking the
        fundamental archetypes we're building today.

        It is perhaps the most important table so far, and replaces the notion
        of 'host' as we've used it in our discussions and designs thus far.
    """
    __tablename__ = 'system'
    _instance_label = 'fqdn'

    id = Column(Integer, Sequence('SYSTEM_SEQ'), primary_key=True)

    name = Column(AqStr(64), nullable=False)

    #TODO: create enum_types for this
    system_type = Column(AqStr(32), nullable=False)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='SYSTEM_DNS_FK'),
                           nullable=False ) #TODO: default

    ip = Column(IPV4, nullable=True)
    network_id = Column(Integer, ForeignKey('network.id',
                                                 name='SYSTEM_NET_ID_FK'),
                                                nullable=True)

    creation_date = deferred(Column( DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column('comments', String(255), nullable=True))

    dns_domain = relation(DnsDomain)
    network = relation(Network, backref='interfaces')

    __mapper_args__ = {'polymorphic_on': system_type}

    @property
    def fqdn(self):
        return '.'.join([str(self.name), str(self.dns_domain.name)])

    @classmethod
    def get_unique(cls, session, *args, **kwargs):
        if "fqdn" in kwargs:
            (name, dbdns_domain) = parse_fqdn(session, kwargs.pop("fqdn"))
            kwargs["name"] = name
            kwargs["dns_domain"] = dbdns_domain
        return super(System, cls).get_unique(session, *args, **kwargs)

    def __init__(self, session=None, *args, **kwargs):
        if "fqdn" in kwargs:
            if not session:
                raise InternalError("Passing fqdn to Session.__init__() needs "
                                    "a session.")
            (name, dbdns_domain) = parse_fqdn(session, kwargs.pop("fqdn"))
            kwargs["name"] = name
            kwargs["dns_domain"] = dbdns_domain
        return super(System, self).__init__(*args, **kwargs)

    @classmethod
    def get_or_create(cls, session, **kwargs):
        system = cls.get_unique(session, **kwargs)
        if system:
            return system
        system = cls(session=session, **kwargs)
        session.add(system)
        session.flush()
        session.refresh(system)
        return system

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(System, self).__format__(format_spec)
        if self.ip:
            return "%s [%s]" % (self.fqdn, self.ip)
        else:
            return self.fqdn


system = System.__table__  # pylint: disable-msg=C0103, E1101
system.primary_key.name = 'SYSTEM_PK'

system.append_constraint(
    UniqueConstraint('name','dns_domain_id', name='SYSTEM_DNS_NAME_UK'))

system.append_constraint(                    #systm_pt_uk means 'primary tuple'
    UniqueConstraint('name', 'dns_domain_id', 'ip', name='SYSTEM_PT_UK'))

system.info['unique_fields'] = ['name', 'dns_domain']
system.info['extra_search_fields'] = ['ip']


class FutureARecord(System):
    """FutureARecord is a placeholder to let us add name/IP addresses now.

    This will be done differently after the DNS revamp.

    """
    __tablename__ = 'future_a_record'
    __mapper_args__ = {'polymorphic_identity': 'future_a_record'}
    _class_label = 'DNS Record'

    system_id = Column(Integer, ForeignKey('system.id',
                                           name='future_a_record_system_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    def __init__(self, ip=None, **kwargs):
        if not ip:  # pragma: no cover
            raise ArgumentError("DNS A records need an IP address.")
        return super(FutureARecord, self).__init__(ip=ip, **kwargs)


farecord = FutureARecord.__table__  # pylint: disable-msg=C0103, E1101
farecord.primary_key.name = 'future_a_record_pk'
farecord.info['unique_fields'] = ['name', 'dns_domain']
farecord.info['extra_search_fields'] = ['ip']


class DynamicStub(FutureARecord):
    """
        DynamicStub is a hack to handle stand alone dns records for dynamic
        hosts prior to having a properly reworked set of tables for Dns
        information. It should not be used by anything other than to create host
        records for virtual machines using names similar to
        'dynamic-1-2-3-4.subdomain.ms.com'
    """
    __tablename__ = 'dynamic_stub'
    __mapper_args__ = {'polymorphic_identity': 'dynamic_stub'}
    _class_label = 'Dynamic Stub'

    system_id = Column(Integer, ForeignKey('future_a_record.system_id',
                                           name='dynamic_stub_farecord_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)


DynamicStub.__table__.primary_key.name = 'dynamic_stub_pk'

Network.dynamic_addresses = relation(DynamicStub, lazy=True, uselist=True,
                                     primaryjoin=and_(DynamicStub.ip >= Network.ip,
                                                      DynamicStub.ip <= Network.broadcast),
                                     foreign_keys=[DynamicStub.ip],
                                     viewonly=True)


class ReservedName(System):
    """
        ReservedName is a placeholder for a name that does not have an IP
        address.
    """

    __tablename__ = 'reserved_name'
    __mapper_args__ = {'polymorphic_identity': 'reserved_name'}
    _class_label = 'Reserved Name'

    system_id = Column(Integer, ForeignKey('system.id',
                                           name='reserved_name_system_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    def __init__(self, **kwargs):
        if "ip" in kwargs and kwargs["ip"]:  # pragma: no cover
            raise ArgumentError("Reserved names must not have an IP address.")
        return super(ReservedName, self).__init__(**kwargs)


resname = ReservedName.__table__  # pylint: disable-msg=C0103, E1101
resname.primary_key.name = 'reserved_name_pk'
resname.info['unique_fields'] = ['name', 'dns_domain']
