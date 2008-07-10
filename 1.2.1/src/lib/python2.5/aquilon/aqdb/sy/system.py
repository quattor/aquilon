#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Systems are higher level constructs which can provide services """
from datetime import datetime

import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

import depends
from db_factory import Base
from column_types.aqstr import AqStr
from net.dns_domain import DnsDomain, dns_domain

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)

from sqlalchemy.orm import relation, deferred, backref

#TODO: enum type for system_type column
#_sys_types = ['host', 'host_list', 'quattor_server']

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

    id            = Column(Integer,
                           Sequence('system_id_seq'), primary_key=True)
    name          = Column(AqStr(64), nullable = False)
    #TODO: create enum_types for this
    system_type   = Column(AqStr(32), nullable = False)
    dns_domain_id = Column(Integer,
                           ForeignKey('dns_domain.id', name = 'sys_dns_fk'),
                           nullable = False ) #TODO: default
    creation_date = deferred(Column( DateTime, default=datetime.now))
    comments      = deferred(Column('comments', String(255), nullable=True))

    dns_domain    = relation(DnsDomain)

    __mapper_args__ = {'polymorphic_on' : system_type}

    def _fqdn(self):
        if self.dns_domain:
            return '.'.join([str(self.name),str(self.dns_domain.name)])
        # FIXME: Is it correct for a system to not have dns_domain?  If
        # it does not have one, should this return name + '.' anyway?
        return str(self.name)
    fqdn = property(_fqdn)

system = System.__table__
system.primary_key.name = 'system_pk'

system.append_constraint(
    UniqueConstraint('name', 'dns_domain_id', 'system_type',
                     name = 'system_name_uk'))

def populate():
    from db_factory import db_factory, Base
    from net.dns_domain import DnsDomain, dns_domain
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    system.create(checkfirst=True)
