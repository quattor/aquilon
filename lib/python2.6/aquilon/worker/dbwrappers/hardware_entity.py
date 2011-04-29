# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

from sqlalchemy.orm import aliased

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (HardwareEntity, Model, DnsRecord, ARecord,
                                ReservedName, AddressAssignment, Fqdn,
                                NetworkEnvironment, Network, Interface, Vendor)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import check_ip_restrictions


def search_hardware_entity_query(session, hardware_type=HardwareEntity,
                                 subquery=False,
                                 model=None, vendor=None, machine_type=None,
                                 exact_location=False,
                                 mac=None, pg=None, serial=None,
                                 interface_model=None, interface_vendor=None,
                                 **kwargs):
    q = session.query(hardware_type)
    if hardware_type is HardwareEntity:
        q = q.with_polymorphic('*')
    dblocation = get_location(session, **kwargs)
    if dblocation:
        if exact_location:
            q = q.filter_by(location=dblocation)
        else:
            childids = dblocation.offspring_ids()
            q = q.filter(HardwareEntity.location_id.in_(childids))
    if model or vendor or machine_type:
        subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                        machine_type=machine_type, compel=True)
        q = q.filter(HardwareEntity.model_id.in_(subq))
    if mac or pg or interface_vendor or interface_model:
        q = q.join('interfaces')
        if mac:
            q = q.filter_by(mac=mac)
        if pg:
            q = q.filter_by(port_group=pg)
        if interface_model or interface_vendor:
            # HardwareEntity also has a .model relation, so we have to be
            # explicit here
            q = q.join(Interface.model)
            if interface_model:
                q = q.filter_by(name=interface_model)
            if interface_vendor:
                a_vendor = aliased(Vendor)
                q = q.join(a_vendor)
                q = q.filter_by(name=interface_vendor)
        q = q.reset_joinpoint()
    if serial:
        q = q.filter_by(serial_no=serial)
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

    dbfqdn = Fqdn.get_or_create(session, fqdn=fqdn)
    dbdns_rec = DnsRecord.get_unique(session, fqdn=dbfqdn)
    dbnet_env = NetworkEnvironment.get_unique_or_default(session)

    if dbdns_rec and dbdns_rec.hardware_entity:
        raise ArgumentError("{0} already exists as the primary name of {1:cl} "
                            "{1.label}.".format(fqdn, dbdns_rec.hardware_entity))
    if ip:
        q = session.query(AddressAssignment)
        q = q.filter_by(ip=ip)
        q = q.join(Network)
        q = q.filter_by(network_environment=dbnet_env)
        addr = q.first()
        if addr:
            raise ArgumentError("IP address {0} is already in use by "
                                "{1:l}.".format(ip, addr.interface))

    if dbdns_rec and isinstance(dbdns_rec, ReservedName) and ip:
        session.delete(dbdns_rec)
        session.flush()
        dbdns_rec = None

    if dbdns_rec:
        # Exclude any other subclasses of DnsRecord except ARecord.
        # Do not use isinstance() here, as DynDnsStub is a child of
        # ARecord
        if dbdns_rec.dns_record_type != 'a_record':
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
            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
            check_ip_restrictions(dbnetwork, ip)
            dbdns_rec = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork)
        else:
            dbdns_rec = ReservedName(fqdn=dbfqdn)
        session.add(dbdns_rec)
        session.flush()
    elif hasattr(dbdns_rec, 'ip'):
        dbnetwork = get_net_id_from_ip(session, dbdns_rec.ip, dbnet_env)
        check_ip_restrictions(dbnetwork, dbdns_rec.ip)

    return dbdns_rec

def convert_primary_name_to_arecord(session, dbhw_ent, ip, dbnetwork):
    # Lock the FQDN, so nothing can steal it while there is no DNS record
    # associated with it
    q = session.query(Fqdn)
    q = q.filter_by(id=dbhw_ent.primary_name.fqdn_id)
    q = q.with_lockmode('update')
    dbfqdn = q.one()

    comments = dbhw_ent.primary_name.comments
    session.delete(dbhw_ent.primary_name)
    session.flush()
    session.expire(dbhw_ent, ['primary_name'])
    session.expire(dbfqdn, ['dns_records'])
    dbdns_rec = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork,
                        comments=comments)
    session.add(dbdns_rec)
    dbhw_ent.primary_name = dbdns_rec
