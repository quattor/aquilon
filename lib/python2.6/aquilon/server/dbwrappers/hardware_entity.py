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
"""Wrappers to make getting and using hardware entities simpler."""


from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.model import (HardwareEntity, Model, System, FutureARecord,
                                ReservedName, AddressAssignment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.interface import check_ip_restrictions


def search_hardware_entity_query(session, hardware_type=HardwareEntity,
                                 subquery=False, **kwargs):
    q = session.query(hardware_type)
    if hardware_type is HardwareEntity:
        q = q.with_polymorphic('*')
    dblocation = get_location(session, **kwargs)
    if dblocation:
        if kwargs.get('exact_location'):
            q = q.filter_by(location=dblocation)
        else:
            childids = dblocation.offspring_ids()
            q = q.filter(HardwareEntity.location_id.in_(childids))
    model = kwargs.get('model', None)
    vendor = kwargs.get('vendor', None)
    machine_type = kwargs.get('machine_type', None)
    if model or vendor or machine_type:
        subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                        machine_type=machine_type, compel=True)
        q = q.filter(HardwareEntity.model_id.in_(subq))
    if kwargs.get('mac') or kwargs.get('pg'):
        q = q.join('interfaces')
        if kwargs.get('mac'):
            q = q.filter_by(mac=kwargs['mac'])
        if kwargs.get('pg'):
            q = q.filter_by(port_group=kwargs['pg'])
        q = q.reset_joinpoint()
    if kwargs.get('serial', None):
        q = q.filter_by(serial_no=kwargs['serial'])
    if not subquery:
        # Oracle does not like "ORDER BY" in a sub-select, so we have to
        # suppress it if we want to use this query as a subquery
        q = q.order_by(HardwareEntity.label)
    return q

def parse_primary_name(session, fqdn, ip):
    """
    Parse & verify a primary name.

    The name may already be registered in the DNS, in which case it must not be
    a primary name of some other hardware. Otherwise, a new DNS record is
    created. If the name already exists as a reserved name and an IP address is
    given, then it is converted to an A record.
    """

    (short, dbdns_domain) = parse_fqdn(session, fqdn)
    dbdns_rec = System.get_unique(session, name=short, dns_domain=dbdns_domain)

    if dbdns_rec and dbdns_rec.hardware_entity:
        raise ArgumentError("{0} already exists as the primary name of "
                            "{1:l}.".format(fqdn, dbdns_rec.hardware_entity))
    if ip:
        addr = session.query(AddressAssignment).filter_by(ip=ip).first()
        if addr:
            raise ArgumentError("IP address {0} is already in use by "
                                "{1:l}.".format(ip, addr.vlan.interface))

    if dbdns_rec and isinstance(dbdns_rec, ReservedName) and ip:
        session.delete(dbdns_rec)
        dbdns_rec = None

    if dbdns_rec:
        # Exclude any other subclasses of System except FutureARecord.
        # Do not use isinstance() here, as DynDnsStub is a child of
        # FutureARecord
        if dbdns_rec.system_type != 'future_a_record':
            raise ArgumentError("%s already exists as a(n) %s." %
                                (fqdn, dbdns_rec._get_class_label()))

        # Make sure the primary name does not resolve to multiple addresses
        if ip and dbdns_rec.ip != ip:
            raise ArgumentError("%s already exists, but points to %s "
                                "instead of %s. A pimary name is not "
                                "allowed to point to multiple addresses." %
                                (fqdn, dbdns_rec.ip, ip))

    if not dbdns_rec:
        if ip:
            dbdns_rec = FutureARecord(name=short, dns_domain=dbdns_domain, ip=ip)
        else:
            dbdns_rec = ReservedName(name=short, dns_domain=dbdns_domain)
        session.add(dbdns_rec)
        session.flush()

    if dbdns_rec.ip:
        dbnetwork = get_net_id_from_ip(session, dbdns_rec.ip)
        check_ip_restrictions(dbnetwork, dbdns_rec.ip)

        # TODO: get rid of this
        dbdns_rec.network = dbnetwork

    return dbdns_rec
