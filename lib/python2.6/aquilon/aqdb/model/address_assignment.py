# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
from ipaddr import IPv4Address
import re

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Sequence,
                        UniqueConstraint)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relation, backref, object_session
from sqlalchemy.sql import and_

from aquilon.aqdb.column_types import IPV4, AqStr
from aquilon.aqdb.model import (Base, Interface, VlanInterface, FutureARecord,
                                Network)

_TN = 'address_assignment'
_ABV = 'addr_assign'


def _address_creator(addr):
    if isinstance(addr, IPv4Address):
        return AddressAssignment(ip=addr, label=None)
    elif isinstance(addr, dict):
        return AddressAssignment(**addr)
    else:  # pragma: no cover
        raise TypeError("Adding an address requires either a bare IP or a "
                        "map containing the IP and the label.")


class AddressAssignment(Base):
    """
        Assignment of IP addresses to network interfaces/VLANs.

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

    vlan_interface_id = Column(Integer, ForeignKey('vlan_interface.id',
                                                   name='%s_vlan_id_fk' % _ABV,
                                                   ondelete='CASCADE'),
                               nullable=False)

    _label = Column("label", AqStr(16), nullable=False)

    ip = Column(IPV4, nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    comments = Column(String(255), nullable=True)

    #TODO: be sure about your cascade behaviors in all cases
    vlan = relation(VlanInterface, lazy=False,
                    backref=backref('assignments', cascade='all, delete-orphan'))

    # Setting passive_deletes is very important here as we do not want the
    # removal of an AddressAssignment record to change the linked System
    # record(s)
    dns_records = relation(FutureARecord, lazy=True, uselist=True,
                           primaryjoin=ip == FutureARecord.ip,
                           foreign_keys=[FutureARecord.ip],
                           passive_deletes=True,
                           backref=backref('assignments', uselist=True))

    fqdns = association_proxy('dns_records', 'fqdn')

    network = relation(Network, lazy=True, uselist=False,
                       primaryjoin=and_(ip >= Network.ip,
                                        ip <= Network.broadcast),
                       foreign_keys=[Network.ip, Network.broadcast],
                       viewonly=True)

    @property
    def logical_name(self):
        """
        Compute an OS-agnostic name for this interface/VLAN/address combo.

        BIG FAT WARNING: do _NOT_ assume that this name really exist on the
        host!

        There are external systems like DSDB that do not understand VLANs, or
        can not handle having multiple addresses on the same interface. Because
        of that this function generates an unique name for every
        interface/vlan/address tuple.

        Note that even if the generated name looks syntactically valid for a
        given host, there is no guarantee that the host really uses this name
        for this interface. The real name used by the OS is determined by the
        templates, but we have no access to that information here.

        For example, a Linux host may have a single "eth0" interface with two
        addresses, instead of having an "eth0" and an "eth0:1" with a single
        address each. A Solaris box (if we ever support that) will have an
        interface called "hme7100000" instead of "hme0.710". So just to repeat,
        the string returned here is purely for inventory reasons, used when
        interfacing with other systems.
        """

        # Use the Linux naming convention because people are familiar with that
        # and it is easy to parse if needed
        name = self.vlan.interface.name
        if self.vlan.vlan_id > 0:
            name += ".%d" % self.vlan.vlan_id
        if self.label:
            name += ":%d" % self.label
        return name

    @property
    def label(self):
        if self._label == '-':
            return ""
        else:
            return self._label

    def __init__(self, label=None, **kwargs):
        # This is dirty. We want to allow empty labels, but Oracle converts
        # empty strings to NULL, violating the NOT NULL constraint. We could
        # allow label to be NULL and relying on the unique indexes to forbid
        # adding multiple empty labels, but that is again Oracle-specific
        # behavior which actually violates the SQL standard, so it would not
        # work with other databases.
        if not label:
            label = '-'
        elif not self._label_check.match(label):
            raise ValueError("Illegal address label '%s'." % label)
        super(AddressAssignment, self).__init__(_label=label, **kwargs)

    def __repr__(self):
        return "<Address %s on %s/%s>" % (self.ip,
                                          self.vlan.interface.hardware_entity.label,
                                          self.logical_name)


address = AddressAssignment.__table__
address.primary_key.name = '%s_pk' % _TN
address.append_constraint(
    UniqueConstraint("vlan_interface_id", "ip", name="%s_vlan_ip_uk" % _ABV))
address.append_constraint(
    UniqueConstraint("vlan_interface_id", "label",
                     name="%s_vlan_label_uk" % _ABV))

# Assigned to external classes here to avoid circular dependencies. See also the
# comments after VlanInterface in vlan.py.
VlanInterface.addresses = association_proxy('assignments', 'ip',
                                            creator=_address_creator)

Network.assignments = relation(AddressAssignment, lazy=True, uselist=True,
                               primaryjoin=and_(AddressAssignment.ip >= Network.ip,
                                                AddressAssignment.ip <= Network.broadcast),
                               foreign_keys=[AddressAssignment.ip],
                               viewonly=True)