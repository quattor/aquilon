# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
""" Assign Addresses to interfaces """

from datetime import datetime
import re

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Sequence,
                        UniqueConstraint)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.sql import and_

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.column_types import IPV4, AqStr
from aquilon.aqdb.model import (Base, Interface, ARecord, DnsEnvironment, Fqdn,
                                Network)
from aquilon.aqdb.model.a_record import dns_fqdn_mapper

_TN = 'address_assignment'
_ABV = 'addr_assign'


class AddressAssignment(Base):
    """
        Assignment of IP addresses to network interfaces.

        It's kept as an association map to model the linkage, since we need to
        have maximum ability to provide potentially complex configuration
        scenarios, such as advertising certain VIP addresses from some, but not
        all of the network interfaces on a machine (to be used for backup
        servers, cluster filesystem servers, NetApp filers, etc.). While in
        most cases we can assume VIPs are broadcast out all interfaces on the
        box we still need to have the underlying model as the more complex
        many to many relationship implemented here.
    """
    __tablename__ = _TN

    _label_check = re.compile('^[a-z0-9]{0,16}$')

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)

    interface_id = Column(Integer, ForeignKey('interface.id',
                                              name='%s_interface_id_fk' % _ABV,
                                              ondelete='CASCADE'),
                          nullable=False)

    _label = Column("label", AqStr(16), nullable=False)

    ip = Column(IPV4, nullable=False)

    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk' % _TN),
                        nullable=False)

    service_address_id = Column(Integer, ForeignKey('service_address.resource_id',
                                                    name='%s_srv_addr_id' % _ABV,
                                                    ondelete="CASCADE"),
                                nullable=True)

    # This should be the same as #
    # network.network_environment.dns_environment_id, but using that would mean
    # joining two extra tables in the dns_records relation
    dns_environment_id = Column(Integer, ForeignKey('dns_environment.id',
                                                    name='%s_dns_env_fk' %
                                                    _ABV),
                                nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    interface = relation(Interface, lazy=False, innerjoin=True,
                         backref=backref('assignments', order_by=[_label],
                                         cascade='all, delete-orphan'))

    dns_environment = relation(DnsEnvironment, innerjoin=True)

    # Setting viewonly is very important here as we do not want the removal of
    # an AddressAssignment record to change the linked DNS record(s)
    # Can't use backref or back_populates due to the different mappers
    dns_records = relation(dns_fqdn_mapper, uselist=True,
                           primaryjoin=and_(ip == ARecord.ip,
                                            dns_environment_id == Fqdn.dns_environment_id),
                           foreign_keys=[ARecord.ip, Fqdn.dns_environment_id],
                           viewonly=True)

    fqdns = association_proxy('dns_records', 'fqdn')

    network = relation(Network, backref=backref('assignments',
                                                passive_deletes=True,
                                                order_by=[ip]))

    @property
    def logical_name(self):
        """
        Compute an OS-agnostic name for this interface/address combo.

        BIG FAT WARNING: do _NOT_ assume that this name really exist on the
        host!

        There are external systems like DSDB that can not handle having multiple
        addresses on the same interface. Because of that this function generates
        an unique name for every interface/address tuple.
        """

        # Use the Linux naming convention because people are familiar with that
        # and it is easy to parse if needed
        name = self.interface.name
        if self.label:
            name += ":%s" % self.label
        return name

    @property
    def label(self):
        if self._label == '-':
            return ""
        else:
            return self._label

    def __init__(self, label=None, network=None, **kwargs):
        # This is dirty. We want to allow empty labels, but Oracle converts
        # empty strings to NULL, violating the NOT NULL constraint. We could
        # allow label to be NULL and relying on the unique indexes to forbid
        # adding multiple empty labels, but that is again Oracle-specific
        # behavior which actually violates the SQL standard, so it would not
        # work with other databases.
        if not label:
            label = '-'
        elif not self._label_check.match(label):  # pragma: no cover
            raise ValueError("Illegal address label '%s'." % label)

        # Right now network_id is nullable due to how refresh_network works, so
        # verify the network here
        if not network:  # pragma: no cover
            raise InternalError("AddressAssignment needs a network")

        super(AddressAssignment, self).__init__(_label=label, network=network,
                                                **kwargs)

    def __repr__(self):
        return "<Address %s on %s/%s>" % (self.ip,
                                          self.interface.hardware_entity.label,
                                          self.logical_name)


address = AddressAssignment.__table__  # pylint: disable=C0103
address.primary_key.name = '%s_pk' % _TN
address.append_constraint(
    UniqueConstraint("interface_id", "ip", name="%s_iface_ip_uk" % _ABV))
address.append_constraint(
    UniqueConstraint("interface_id", "label", name="%s_iface_label_uk" % _ABV))

# Assigned to external classes here to avoid circular dependencies.
Interface.addresses = association_proxy('assignments', 'ip')

# Can't use backref or back_populates due to the different mappers
# This relation gives us the two other sides of the triangle mentioned above
ARecord.assignments = relation(
    AddressAssignment,
    primaryjoin=and_(AddressAssignment.ip == ARecord.ip,
                     AddressAssignment.network_id == ARecord.network_id,
                     ARecord.fqdn_id == Fqdn.id,
                     AddressAssignment.dns_environment_id == Fqdn.dns_environment_id),
    foreign_keys=[AddressAssignment.ip, AddressAssignment.network_id, Fqdn.id],
    viewonly=True)
