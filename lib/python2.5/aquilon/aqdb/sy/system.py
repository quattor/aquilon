""" Systems are higher level constructs which can provide services """
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.column_types.IPV4  import IPV4
from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.net.dns_domain     import DnsDomain
from aquilon.aqdb.net.network        import Network

#TODO: enum type for system_type column
#_sys_types = ['host', 'tor_switch', 'console_switch', 'chassis', 'manager',
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

    id              = Column(Integer,
                           Sequence('SYSTEM_SEQ'), primary_key=True)

    name            = Column(AqStr(64), nullable = False)

    #TODO: create enum_types for this
    system_type     = Column(AqStr(32), nullable = False)

    dns_domain_id   = Column(Integer,
                           ForeignKey('dns_domain.id', name = 'SYSTEM_DNS_FK'),
                           nullable = False ) #TODO: default

    mac             = Column(AqMac(17), nullable = True)
    ip              = Column(IPV4, nullable = True)
    network_id      = Column(Integer, ForeignKey('network.id',
                                                 name = 'SYSTEM_NET_ID_FK'),
                                                nullable = True)

    creation_date   = deferred(Column( DateTime, default = datetime.now,
                                    nullable = False))

    comments        = deferred(Column('comments', String(255), nullable=True))

    dns_domain      = relation(DnsDomain)
    network         = relation(Network, backref = 'interfaces')

    __mapper_args__ = {'polymorphic_on' : system_type}

    def _fqdn(self):
        return '.'.join([str(self.name),str(self.dns_domain.name)])
    fqdn = property(_fqdn)

system = System.__table__
system.primary_key.name = 'SYSTEM_PK'

system.append_constraint(
    # Removing type. Unsure it's needed
    #    UniqueConstraint('name', 'dns_domain_id', 'system_type',
    UniqueConstraint('name','dns_domain_id', name = 'SYSTEM_DNS_NAME_UK'))

system.append_constraint(                    #systm_pt_uk means 'primary tuple'
    UniqueConstraint('name', 'dns_domain_id', 'mac', 'ip', name='SYSTEM_PT_UK'))

table = system

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
