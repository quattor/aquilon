# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import aliased, contains_eager, joinedload
from sqlalchemy.sql import and_, or_

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import (HardwareEntity, Model, ReservedName, Network,
                                AddressAssignment, ARecord, Fqdn, Interface,
                                VlanInfo, PortGroup, NetworkEnvironment, Host)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.dns import convert_reserved_to_arecord
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (check_ip_restrictions,
                                                 assign_address)
from aquilon.worker.dbwrappers.network import get_network_byip
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.utils import first_of


def search_hardware_entity_query(session, hardware_type=HardwareEntity,
                                 subquery=False,
                                 model=None, vendor=None, machine_type=None,
                                 exact_location=False, ip=None, networkip=None,
                                 network_environment=None,
                                 mac=None, pg=None, serial=None,
                                 interface_name=None, interface_model=None,
                                 interface_vendor=None,
                                 interface_bus_address=None,
                                 used=None,
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
                                        model_type=machine_type, compel=True)
        q = q.filter(HardwareEntity.model_id.in_(subq))
    if ip or networkip or mac or pg or interface_name or interface_vendor \
       or interface_model or interface_bus_address:
        IfaceAlias = aliased(Interface)
        q = q.join(IfaceAlias, HardwareEntity.interfaces)
        if mac:
            q = q.filter_by(mac=mac)
        if interface_name:
            q = q.filter_by(name=interface_name)
        if interface_bus_address:
            q = q.filter_by(bus_address=interface_bus_address)
        if pg:
            filters = [IfaceAlias.port_group_name == pg]

            dbvi = VlanInfo.get_by_pg(session, pg, compel=False)
            if dbvi:
                filters.append(and_(PortGroup.network_tag == dbvi.vlan_id,
                                    PortGroup.usage == dbvi.vlan_type))
            else:
                usage, network_tag = PortGroup.parse_name(pg)
                if network_tag is not None:
                    filters.append(and_(PortGroup.network_tag == network_tag,
                                        PortGroup.usage == usage))
                else:
                    filters.append(PortGroup.usage == pg)

            q = q.outerjoin(PortGroup, aliased=True, from_joinpoint=True)
            q = q.filter(or_(*filters))
            q = q.reset_joinpoint()
        if interface_model or interface_vendor:
            subq = Model.get_matching_query(session, name=interface_model,
                                            vendor=interface_vendor,
                                            model_type='nic', compel=True)
            q = q.filter(IfaceAlias.model_id.in_(subq))
        if ip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                                 network_environment)
            q = q.join(AddressAssignment, aliased=True, from_joinpoint=True)
            q = q.filter_by(ip=ip)
            q = q.join(Network, aliased=True, from_joinpoint=True)
            q = q.filter_by(network_environment=dbnet_env)
        elif networkip:
            dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                                 network_environment)
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
            PGAlias = aliased(PortGroup)
            AAAlias = aliased(AddressAssignment)
            q = q.outerjoin(PGAlias, IfaceAlias.port_group)
            q = q.outerjoin(AAAlias, IfaceAlias.assignments)
            q = q.filter(or_(PGAlias.network == dbnetwork,
                             AAAlias.network == dbnetwork))
        q = q.reset_joinpoint()

    if serial:
        q = q.filter_by(serial_no=serial)

    if used is True:
        q = q.join(Host, aliased=True)
        q = q.reset_joinpoint()
    elif used is False:
        q = q.outerjoin(Host, aliased=True)
        q = q.filter_by(hardware_entity_id=None)

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
    q = q.filter_by(network=dbnetwork, ip=ip)
    addr = q.first()
    if addr:
        raise ArgumentError("IP address {0} is already in use by {1:l}."
                            .format(ip, addr.interface))

    # We can't steal the IP address from an existing DNS entry
    q = session.query(ARecord)
    q = q.filter_by(network=dbnetwork, ip=ip)
    q = q.join(ARecord.fqdn)
    q = q.filter_by(dns_environment=dbhw_ent.primary_name.fqdn.dns_environment)
    existing = q.first()
    if existing:
        raise ArgumentError("IP address {0!s} is already used by "
                            "{1:l}." .format(ip, existing))

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

        if type(dns_rec.ip) is not type(ip):
            raise ArgumentError("Changing the IP address type is not allowed.")

        q = session.query(AddressAssignment)
        q = q.filter_by(network=dns_rec.network)
        q = q.filter_by(ip=dns_rec.ip)
        q = q.join(Interface)
        q = q.options(contains_eager('interface'),
                      joinedload('interface.port_group'))
        q = q.filter_by(hardware_entity=dbhw_ent)
        addrs = q.all()

        dns_rec.ip = ip
        dns_rec.network = dbnetwork

        for addr in addrs:
            addr.ip = ip
            addr.network = dbnetwork

        for iface in set(addr.interface for addr in addrs):
            iface.check_pg_consistency(logger=logger)


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

    new_hw = HardwareEntity.get_unique(session, new_label)
    old_label = dbhw_ent.label

    if new_hw and new_hw.label != old_label:
        raise ArgumentError('{0} already exists.'.format(new_hw))

    fqdns = []
    for addr in dbhw_ent.all_addresses():
        fqdns.extend(dns_rec.fqdn for dns_rec in addr.dns_records)
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


def check_only_primary_ip(dbhw_ent):
    """Check and complain if the hardware entity has any other addresses
       assignments other than its primary address.
    """
    addrs = []
    for addr in dbhw_ent.all_addresses():
        if addr.ip == dbhw_ent.primary_ip:
            continue
        addrs.append(str(addr.ip))
    if addrs:
        raise ArgumentError("{0} still provides the following addresses, "
                            "delete them first: {1}.".format
                            (dbhw_ent, ", ".join(sorted(addrs))))


def get_hardware(session, compel=True, hostname=None, **kwargs):
    """
    Get HardwareEntity by hostname, machine name, chassis name
    or network device name
    """
    if hostname:
        dbhost = hostname_to_host(session, hostname)
        return dbhost.hardware_entity

    mapper = inspect(HardwareEntity)

    dbhw_ent = None
    for hw_type, submapper in mapper.polymorphic_map.items():
        if hw_type not in kwargs or not kwargs[hw_type]:
            continue

        if dbhw_ent:
            raise ArgumentError("Multiple devices are specified.")
        dbhw_ent = submapper.class_.get_unique(session, kwargs[hw_type],
                                               compel=True)
    if not dbhw_ent and compel:
        raise ArgumentError("Please specify a device.")

    return dbhw_ent
