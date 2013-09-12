# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wrappers to make getting and using hardware entities simpler."""

from sqlalchemy.orm import aliased

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import (HardwareEntity, Model, ReservedName,
                                AddressAssignment, Fqdn, Interface, Vendor)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.dns import convert_reserved_to_arecord
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (check_ip_restrictions,
                                                 assign_address)
from aquilon.utils import first_of


def search_hardware_entity_query(session, hardware_type=HardwareEntity,
                                 subquery=False,
                                 model=None, vendor=None, machine_type=None,
                                 exact_location=False, ip=None,
                                 mac=None, pg=None, serial=None,
                                 interface_model=None, interface_vendor=None,
                                 **kwargs):
    q = session.query(hardware_type)
    if hardware_type is HardwareEntity:
        q = q.with_polymorphic('*')

    # The ORM deduplicates the result if we query full objects, but not if we
    # query just the label
    q = q.distinct()

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
    if ip or mac or pg or interface_vendor or interface_model:
        q = q.join('interfaces')
        if mac:
            q = q.filter_by(mac=mac)
        if pg:
            q = q.filter_by(port_group=pg)
        if ip:
            q = q.join(AddressAssignment)
            q = q.filter(AddressAssignment.ip == ip)
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


def update_primary_ip(session, logger, dbhw_ent, ip):
    if not dbhw_ent.primary_name:
        raise ArgumentError("{0} does not have a primary name."
                            .format(dbhw_ent))

    dbnetwork = get_net_id_from_ip(session, ip)
    check_ip_restrictions(dbnetwork, ip)

    # The primary address must be unique
    q = session.query(AddressAssignment)
    q = q.filter_by(network=dbnetwork)
    q = q.filter_by(ip=ip)
    addr = q.first()
    if addr:
        raise ArgumentError("IP address {0} is already in use by {1:l}."
                            .format(ip, addr.interface))

    # Convert ReservedName to ARecord if needed
    if isinstance(dbhw_ent.primary_name, ReservedName):
        convert_reserved_to_arecord(session, dbhw_ent.primary_name, dbnetwork,
                                    ip)

        # When converting a ReservedName to an ARecord, we have to bind the
        # primary address to an interface. Try to pick one.
        dbinterface = first_of(dbhw_ent.interfaces, lambda x: x.bootable)
        if not dbinterface:
            dbinterface = first_of(dbhw_ent.interfaces, lambda x:
                                   x.interface_type != "management")

        if not dbinterface:  # pragma: no cover
            raise AquilonError("Cannot update the primary IP address of {0:l} "
                               "because it does not have any interfaces "
                               "defined.".format(dbhw_ent))

        assign_address(dbinterface, ip, dbnetwork, logger=logger)
    else:
        dns_rec = dbhw_ent.primary_name

        q = session.query(AddressAssignment)
        q = q.filter_by(network=dns_rec.network)
        q = q.filter_by(ip=dns_rec.ip)
        q = q.join(Interface)
        q = q.filter_by(hardware_entity=dbhw_ent)
        # In case of Zebra, the address may be assigned to multiple interfaces
        addrs = q.all()

        dns_rec.ip = ip
        dns_rec.network = dbnetwork

        for addr in addrs:
            addr.ip = ip
            addr.network = dbnetwork


def rename_hardware(session, dbhw_ent, rename_to):
    if "." in rename_to:
        if not dbhw_ent.primary_name:
            raise ArgumentError("{0} does not have a primary name, renaming "
                                "using an FQDN is not possible."
                                .format(dbhw_ent))
        old_domain = dbhw_ent.primary_name.fqdn.dns_domain
        dns_env = dbhw_ent.primary_name.fqdn.dns_environment
        new_label, new_domain = parse_fqdn(session, rename_to)
    else:
        new_label = rename_to
        if dbhw_ent.primary_name:
            old_domain = new_domain = dbhw_ent.primary_name.fqdn.dns_domain
            dns_env = dbhw_ent.primary_name.fqdn.dns_environment
        else:
            new_domain = None
            dns_env = None

    old_domain.lock_row()
    if new_domain != old_domain:
        new_domain.lock_row()

    dbhw_ent.check_label(new_label)
    HardwareEntity.get_unique(session, new_label, preclude=True)

    old_label = dbhw_ent.label

    fqdns = []
    for addr in dbhw_ent.all_addresses():
        fqdns.extend([dns_rec.fqdn for dns_rec in addr.dns_records])
    # This case handles reserved names
    if dbhw_ent.primary_name and dbhw_ent.primary_name.fqdn not in fqdns:
        fqdns.append(dbhw_ent.primary_name.fqdn)

    # Filter out unrelated FQDNs
    fqdns = [fqdn for fqdn in fqdns if fqdn.dns_domain == old_domain and
             (fqdn.name == old_label or fqdn.name.startswith(old_label + "-"))]

    # Update all state in one go, so disable autoflush for now.
    with session.no_autoflush:
        dbhw_ent.label = new_label

        for dbfqdn in fqdns:
            new_name = new_label + dbfqdn.name[len(old_label):]
            Fqdn.get_unique(session, name=new_name, dns_domain=new_domain,
                            dns_environment=dns_env, preclude=True)
            dbfqdn.dns_domain = new_domain
            dbfqdn.name = new_name
