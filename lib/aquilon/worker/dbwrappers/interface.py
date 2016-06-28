# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Wrapper to make getting an interface simpler.

To an extent, this has become a dumping ground for any common ip methods.

"""

from operator import attrgetter
import re

from ipaddr import IPv4Address

from sqlalchemy.orm import aliased, object_session
from sqlalchemy.sql.expression import desc, type_coerce

from aquilon.exceptions_ import ArgumentError, InternalError, AquilonError
from aquilon.config import Config
from aquilon.aqdb.types import NicType, MACAddress
from aquilon.aqdb.column_types import AqMac
from aquilon.aqdb.model import (Interface, ManagementInterface, ObservedMac,
                                Fqdn, ARecord, VlanInfo, AddressAssignment,
                                SharedAddressAssignment,
                                Model, Bunker, Location, HardwareEntity,
                                Network, Host)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.utils import first_of


_vlan_re = re.compile(r'^(.*)\.(\d+)$')


def check_ip_restrictions(dbnetwork, ip, relaxed=False):
    """ given a network and ip addr, raise an exception if the ip is reserved

        Used during ip assignment as a check against grabbing an ip address
        that we have reserved as a dynamic dhcp pool for switches (and
        potentially other assorted devices) The remainder of addresses are to
        be used for static assignment (for telco gear only).

        Setting relaxed to true means checking only the most obvious problems.
    """

    # TODO: if the network type doesn't have any applicable offsets, we
    # probably want to reserve the first ip for the gateway on all networks
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return

    if ip < dbnetwork.ip or ip > dbnetwork.broadcast:  # pragma: no cover
        raise InternalError("IP address {0!s} is outside "
                            "{1:l}.".format(ip, dbnetwork))
    if dbnetwork.network.numhosts >= 4 and not relaxed:
        # Skip these checks for /32 and /31 networks
        if ip == dbnetwork.ip:
            raise ArgumentError("IP address %s is the address of network %s." %
                                (ip, dbnetwork.name))
        if ip == dbnetwork.broadcast:
            raise ArgumentError("IP address %s is the broadcast address of "
                                "network %s." % (ip, dbnetwork.name))

    if dbnetwork.network.numhosts >= 8 and not relaxed:
        # If this network doesn't have enough addresses, the test is irrelevant.
        if int(ip) - int(dbnetwork.ip) in dbnetwork.reserved_offsets:
            raise ArgumentError("The IP address %s is reserved for dynamic "
                                "DHCP for a switch on subnet %s." %
                                (ip, dbnetwork.ip))
    return


def get_cluster_pg_allocator(dbcluster):
    if dbcluster.virtual_switch:
        return dbcluster.virtual_switch
    if dbcluster.metacluster and dbcluster.metacluster.virtual_switch:
        return dbcluster.metacluster.virtual_switch
    # Fallback
    if dbcluster.network_device:
        return dbcluster.network_device

    raise ArgumentError("{0} does not have either a virtual switch or a "
                        "network device assigned, automatic IP address "
                        "and port group allocation is not possible."
                        .format(dbcluster))


def get_host_pg_allocator(dbhost):
    if dbhost.virtual_switch:
        return dbhost.virtual_switch
    if dbhost.cluster:
        return get_cluster_pg_allocator(dbhost.cluster)
    raise ArgumentError("{0} does not have a virtual switch assigned and "
                        "is not part of a cluster either, automatic IP "
                        "address and port group allocation is not possible."
                        .format(dbhost))


def get_vm_pg_allocator(dbmachine):
    holder = dbmachine.vm_container.holder.toplevel_holder_object
    if isinstance(holder, Host):
        return get_host_pg_allocator(holder)
    else:
        return get_cluster_pg_allocator(holder)


def generate_ip(session, logger, dbinterface, ip=None, ipfromip=None,
                ipfromsystem=None, autoip=None, ipalgorithm=None, compel=False,
                network_environment=None, audit_results=None, **_):
    ip_options = [ip, ipfromip, ipfromsystem, autoip]
    numopts = sum(1 if opt else 0 for opt in ip_options)
    if numopts > 1:
        raise ArgumentError("Only one of --ip, --ipfromip, --ipfromsystem "
                            "and --autoip can be specified.")
    elif numopts == 0:
        if compel:
            raise ArgumentError("Please specify one of the --ip, --ipfromip, "
                                "--ipfromsystem, and --autoip parameters.")
        return None

    if ip:
        return ip

    dbnetwork = None
    if autoip:
        if not dbinterface:
            raise ArgumentError("No interface available to automatically "
                                "generate an IP address.")
        if dbinterface.port_group:
            # VM
            dbnetwork = dbinterface.port_group.network
        elif dbinterface.port_group_name:
            # Physical host
            dbhw_ent = dbinterface.hardware_entity
            if not dbhw_ent.host:
                raise ArgumentError("{0} does not have a host, assigning an IP "
                                    "address based on port group membership is "
                                    "not possible.".format(dbhw_ent))
            allocator = get_host_pg_allocator(dbhw_ent.host)

            dbvi = VlanInfo.get_by_pg(session, dbinterface.port_group_name)

            pg = first_of(allocator.port_groups,
                          lambda x: x.network_tag == dbvi.vlan_id)

            if not pg:
                raise ArgumentError("No network found for {0:l} and port "
                                    "group {1}".format(allocator,
                                                       dbinterface.pot_group_name))
            dbnetwork = pg.network
        elif dbinterface.mac:
            q = session.query(ObservedMac)
            q = q.filter_by(mac_address=dbinterface.mac)
            q = q.order_by(desc(ObservedMac.last_seen))
            dbom = q.first()
            if not dbom:
                raise ArgumentError("No switch found in the discovery table "
                                    "for MAC address %s." % dbinterface.mac)
            if not dbom.network_device.primary_ip:
                raise ArgumentError("{0} does not have a primary IP address "
                                    "to use for network "
                                    "selection.".format(dbom.network_device))
            dbnetwork = get_net_id_from_ip(session,
                                           dbom.network_device.primary_ip)
        else:
            raise ArgumentError("{0} has neither a MAC address nor port group "
                                "information, it is not possible to generate "
                                "an IP address automatically."
                                .format(dbinterface))

    if ipfromsystem:
        # Assumes one system entry, not necessarily correct.
        dbdns_rec = ARecord.get_unique(session, fqdn=ipfromsystem, compel=True)
        dbnetwork = dbdns_rec.network

    if ipfromip:
        # determine network
        dbnetwork = get_net_id_from_ip(session, ipfromip, network_environment)

    if not dbnetwork:  # pragma: no cover
        raise ArgumentError("Could not determine network to use for %s." %
                            dbinterface)

    # When there are e.g. multiple "add manager --autoip" operations going on in
    # parallel, we must ensure that they won't try to use the same IP address.
    # This query places a database lock on the network, which means IP address
    # generation within a network will be serialized, while operations on
    # different networks can still run in parallel. The lock will be released by
    # COMMIT or ROLLBACK.
    dbnetwork.lock_row()

    startip = dbnetwork.first_usable_host

    used_ips = session.query(ARecord.ip)
    used_ips = used_ips.filter_by(network=dbnetwork)
    used_ips = used_ips.filter(ARecord.ip >= startip)

    full_set = set(range(int(startip), int(dbnetwork.broadcast)))
    used_set = set(int(item.ip) for item in used_ips)
    free_set = full_set - used_set

    if not free_set:
        raise ArgumentError("No available IP addresses found on "
                            "network %s." % str(dbnetwork.network))

    if ipalgorithm is None or ipalgorithm == 'lowest':
        # Select the lowest available address
        ip = IPv4Address(min(free_set))
    elif ipalgorithm == 'highest':
        # Select the highest available address
        ip = IPv4Address(max(free_set))
    elif ipalgorithm == 'max':
        # Return the max. used address + 1
        if not used_set:
            # Avoids ValueError being thrown when used_set is empty
            ip = IPv4Address(min(free_set))
        else:
            next = max(used_set)
            if not next + 1 in free_set:
                raise ArgumentError("Failed to find an IP that is suitable "
                                    "for --ipalgorithm=max.  Try an other "
                                    "algorithm as there are still some free "
                                    "addresses.")
            ip = IPv4Address(next + 1)
    else:
        raise ArgumentError("Unknown algorithm %s." % ipalgorithm)

    if audit_results is not None:
        if dbinterface:
            logger.info("Selected IP address {0!s} for {1:l}."
                        .format(ip, dbinterface))
        else:
            logger.info("Selected IP address %s." % ip)
        audit_results.append(('ip', ip))

    return ip


def set_port_group_phys(session, dbinterface, port_group_name):
    # Physical interface must use a pre-registered port group name
    dbvi = VlanInfo.get_by_pg(session, port_group=port_group_name,
                              compel=ArgumentError)
    dbmachine = dbinterface.hardware_entity
    dbhost = dbmachine.host

    if dbhost:
        allocator = get_host_pg_allocator(dbhost)
        pg = first_of(allocator.port_groups,
                      lambda x: x.network_tag == dbvi.vlan_id)
        if not pg:
            raise ArgumentError("{0} does not have port group {1!s} assigned."
                                .format(allocator, port_group_name))

    dbinterface.port_group = None
    dbinterface.port_group_name = dbvi.port_group


def set_port_group_vm(session, logger, dbinterface, port_group_name):
    dbmachine = dbinterface.hardware_entity
    allocator = get_vm_pg_allocator(dbmachine)
    dbvi = VlanInfo.get_by_pg(session, port_group=port_group_name, compel=None)
    if dbvi:
        # User requested a specific VLAN, check if it is available
        selected_pg = first_of(allocator.port_groups,
                               lambda x: x.network_tag == dbvi.vlan_id)
        if not selected_pg:
            raise ArgumentError("Cannot verify port group availability: "
                                "no record for VLAN {0} on "
                                "{1:l}.".format(dbvi.vlan_id, allocator))

        # The capacity check below would account this interface twice if we'd
        # try to assign the same port group as it already has
        if dbinterface.port_group == selected_pg:
            return

        # Protect against concurrent allocations
        selected_pg.network.lock_row()

        if selected_pg.network.is_at_guest_capacity:
            raise ArgumentError("{0} is full for {1:l}.".format(selected_pg,
                                                                allocator))
    else:
        config = Config()
        vlan_types = [vlan.strip()
                      for vlan in config.get("broker", "vlan_types").split(",")
                      if vlan.strip()]
        if port_group_name not in vlan_types:
            raise ArgumentError("Port group %s does not match either a "
                                "registered port group name, or a port "
                                "group type." % port_group_name)

        # If the current port group matches the requirements, then we're done.
        if dbinterface.port_group in allocator.port_groups and \
           dbinterface.port_group.name == port_group_name:
            return

        selected_pg = None
        selected_capacity = 0

        # Protect agains concurrent invocations
        Network.lock_rows(pg.network for pg in allocator.port_groups)

        used_pgs = set(iface.port_group for iface in dbmachine.interfaces
                       if iface.port_group)
        usable_pgs = set(allocator.port_groups)
        usable_pgs -= used_pgs

        for pg in sorted(usable_pgs, key=attrgetter('network_tag')):
            if pg.usage != port_group_name:
                continue
            net = pg.network
            free_capacity = net.available_ip_count - net.guest_count
            if free_capacity > 0 and selected_capacity < free_capacity:
                selected_pg = pg
                selected_capacity = free_capacity

        if not selected_pg:
            raise ArgumentError("No available {0!s} port groups on {1:l}."
                                .format(port_group_name, allocator))

        logger.info("Selected {0:l} for {1:l} (based on {2:l})."
                    .format(selected_pg, dbinterface, allocator))

    dbinterface.port_group_name = None
    dbinterface.port_group = selected_pg


def set_port_group(session, logger, dbinterface, port_group_name,
                   check_pg_consistency=True):
    """Validate that the port_group can be used on an interface.

    If the machine is virtual, check that the corresponding VLAN has
    been observed on the cluster's switch.

    If the machine is physical but is part of an ESX cluster, also
    check that the VLAN has been observed.

    Otherwise just accept the label.

    As a convenience, return None (unset the port_group) if an empty
    string is passed in.

    """
    if "port_group_name" not in dbinterface.extra_fields:
        raise ArgumentError("The port group cannot be set for %s interfaces." %
                            dbinterface.interface_type)

    if not port_group_name:
        if dbinterface.port_group:
            dbinterface.port_group = None
        else:
            dbinterface.port_group_name = None
        return

    session = object_session(dbinterface)

    if dbinterface.hardware_entity.model.model_type.isVirtualMachineType():
        set_port_group_vm(session, logger, dbinterface, port_group_name)
    else:
        set_port_group_phys(session, dbinterface, port_group_name)

    if check_pg_consistency:
        dbinterface.check_pg_consistency(logger=logger)


def _type_msg(interface_type, bootable):
    if bootable is not None:
        return "%s, %s" % ("bootable" if bootable else "non-bootable",
                           interface_type)
    else:
        return interface_type


def get_or_create_interface(session, dbhw_ent, name=None, mac=None,
                            model=None, vendor=None, bus_address=None,
                            interface_type='public', bootable=None,
                            preclude=False, comments=None):
    """
    Look up an existing interface or create a new one.

    If either the name or the MAC address is given and a matching interface
    exists, then that interface is returned and the other parameters are not
    checked.

    If neither the name nor the MAC address is given, but there is just one
    existing interface matching the specified interface_type/bootable
    combination, then that interface is returned. If there are multiple matches,
    an exception is raised.

    If no interfaces were found, and enough parameters are provided, then a new
    interface is created. For this purpose, at least the name and in some cases
    the MAC address must be specified.

    Setting preclude to True enforces the creation of a new interface. An error
    is raised if a conflicting interface already exists.
    """

    # The database enforces lower case strings for the (interface) name.  Force
    # the passed name to lower case for comparisons.
    if name:
        name = name.strip().lower()

    dbinterface = None
    if mac:
        # Look for the MAC globally. If it is present, check that it belongs to
        # the right hardware, and that it does not conflict with the name (if
        # any).
        q = session.query(Interface)
        q = q.filter_by(mac=mac)
        dbinterface = q.first()
        if dbinterface and (dbinterface.hardware_entity != dbhw_ent or
                            (name and dbinterface.name != name)):
            raise ArgumentError("MAC address {0!s} is already used by {1:l}."
                                .format(mac, dbinterface))

    if name and not dbinterface:
        for iface in dbhw_ent.interfaces:
            if iface.name == name:
                dbinterface = iface
                break

    if not name and not mac:
        # Time for guessing. If neither the name nor the MAC was given, then
        # there is no guarantee of uniqueness, but we can still return something
        # useful if e.g. there is just one management interface.
        interfaces = []
        for iface in dbhw_ent.interfaces:
            if iface.interface_type != interface_type:
                continue
            if bootable is not None and (not hasattr(iface, "bootable") or
                                         iface.bootable != bootable):
                continue
            interfaces.append(iface)
        if len(interfaces) > 1:
            type_msg = _type_msg(interface_type, bootable)
            raise ArgumentError("{0} has multiple {1} interfaces, please "
                                "specify which one to "
                                "use.".format(dbhw_ent, type_msg))
        elif interfaces:
            dbinterface = interfaces[0]
        else:
            dbinterface = None

    if dbinterface:
        if preclude:
            raise ArgumentError("{0} already exists.".format(dbinterface))
        return dbinterface

    # No suitable interface was found, try to create a new one

    if not name:
        # Not enough information to create it
        type_msg = _type_msg(interface_type, bootable)
        raise ArgumentError("{0} has no {1} interfaces.".format(dbhw_ent,
                                                                type_msg))

    cls = Interface.polymorphic_subclass(interface_type,
                                         "Invalid interface type")
    extra_args = {}
    default_route = False
    if bootable is not None:
        extra_args["bootable"] = bootable
        default_route = bootable

    if not model and not vendor:
        dbmodel = dbhw_ent.model.nic_model
    elif not cls.model_allowed:
        raise ArgumentError("Model/vendor can not be set for a %s." %
                            cls._get_class_label(tolower=True))
    else:
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   model_type=NicType.Nic, compel=True)

    # VLAN interfaces need some special handling
    if interface_type == 'vlan':
        result = _vlan_re.match(name)
        if not result:
            raise ArgumentError("Invalid VLAN interface name '%s'." % name)
        parent_name = result.groups()[0]
        vlan_id = int(result.groups()[1])

        dbparent = None
        for iface in dbhw_ent.interfaces:
            if iface.name == parent_name:
                dbparent = iface
                break
        if not dbparent:
            raise ArgumentError("Parent interface %s for VLAN interface %s "
                                "does not exist, please create it first." %
                                (parent_name, name))

        extra_args["parent"] = dbparent
        extra_args["vlan_id"] = vlan_id

    for key in extra_args:
        if key not in cls.extra_fields:
            raise InternalError("Parameter %s is not valid for %s "
                                "interfaces." % (key, interface_type))

    try:
        dbinterface = cls(name=name, mac=mac, comments=comments, model=dbmodel,
                          bus_address=bus_address, default_route=default_route,
                          **extra_args)
    except ValueError as err:
        raise ArgumentError(err)

    dbhw_ent.interfaces.append(dbinterface)
    session.flush()
    return dbinterface


def enforce_bucket_alignment(dbrack, dbnetwork, logger):
    net_loc = dbnetwork.location
    net_bunker = net_loc.bunker
    rack_bunker = dbrack.bunker

    if not net_bunker:
        # The simple case - no alignment is needed
        if not rack_bunker:
            return

        # The second easiest case - the rack is in a bunker, but the network is
        # not
        logger.warning("Bunker violation: {0:l} is inside {1:l}, but {2:l} is "
                       "not bunkerized.".format(dbrack, rack_bunker, dbnetwork))
        return

    session = object_session(dbrack)

    if dbnetwork.may_span_buildings and "." in net_bunker.name:
        # If a network spans buildings, we pretend it's in the bunker local to
        # the rack's building, even if it was registered to the other side. This
        # hack could be removed if we had buckets as a Location subclass.
        bucket, _ = net_bunker.name.split(".", 1)
        expected_bunker = Bunker.get_unique(session, bucket + "." +
                                            dbrack.building.name, compel=True)
    else:
        expected_bunker = net_bunker

    if not rack_bunker:
        # The rack is not inside a bunker yet. If there's only one machine
        # inside the rack, then we can just set the bunker based on the
        # network's bucket - since we'll in the middle of an address assignment,
        # the plenary of the machine (if any) will be rewritten anyway.
        q = session.query(HardwareEntity)
        q = q.join(Location)
        q = q.filter(Location.id.in_(dbrack.offspring_ids()))
        if q.count() > 1:
            logger.warning("Bunker violation: {0:l} is inside {1:l}, "
                           "but {2:l} is not inside a bunker."
                           .format(dbnetwork, net_bunker, dbrack))
            return

        logger.client_info("Moving {0:l} into {1:l} based on network tagging."
                           .format(dbrack, expected_bunker))
        dbrack.update_parent(parent=expected_bunker)
        rack_bunker = expected_bunker

    if rack_bunker != expected_bunker:
        logger.warning("Bunker violation: {0:l} is inside {1:l}, but "
                       "{2:l} is inside {3:l}."
                       .format(dbrack, rack_bunker, dbnetwork,
                               expected_bunker))


def assign_address(dbinterface, ip, dbnetwork, label=None, shared=False,
                   priority=None, logger=None):
    assert isinstance(dbinterface, Interface)

    if dbinterface.master:
        raise ArgumentError("Slave interfaces cannot hold addresses.")

    dbrack = dbinterface.hardware_entity.location.rack

    # Do not enforce bucket alignment for OOB management interfaces. We may want
    # to make that configurable in the future.
    if dbrack and not isinstance(dbinterface, ManagementInterface):
        enforce_bucket_alignment(dbrack, dbnetwork, logger)

    dbinterface.validate_network(dbnetwork)

    for addr in dbinterface.assignments:
        if not label and not addr.label:
            raise ArgumentError("{0} already has an IP "
                                "address.".format(dbinterface))
        if label and addr.label == label:
            raise ArgumentError("{0} already has an alias named "
                                "{1}.".format(dbinterface, label))
        if addr.ip == ip:
            raise ArgumentError("{0} already has IP address {1} "
                                "configured.".format(dbinterface, ip))

    if shared:
        dbinterface.assignments.append(SharedAddressAssignment(ip=ip, network=dbnetwork,
                                                               label=label,
                                                               priority=priority))
    else:
        dbinterface.assignments.append(AddressAssignment(ip=ip, network=dbnetwork,
                                                         label=label))
    dbinterface.check_pg_consistency(logger=logger)


def rename_interface(session, dbinterface, rename_to):
    rename_to = rename_to.strip().lower()

    dbhw_ent = dbinterface.hardware_entity
    for iface in dbhw_ent.interfaces:
        if iface.name == rename_to:
            raise ArgumentError("{0} already has an interface named {1}."
                                .format(dbhw_ent, rename_to))

    fqdn_changes = []

    if dbhw_ent.primary_name:
        primary_fqdn = dbhw_ent.primary_name.fqdn
        short = primary_fqdn.name
        dbdns_domain = primary_fqdn.dns_domain
        dbdns_env = primary_fqdn.dns_environment

        dbdns_domain.lock_row()

        # Rename DNS entries that follow the standard naming convention, except
        # the primary name. The primary name should not have an interface
        # suffix, but who knows...
        for addr in dbinterface.assignments:
            if addr.label:
                old_name = "%s-%s-%s" % (short, dbinterface.name, addr.label)
                new_name = "%s-%s-%s" % (short, rename_to, addr.label)
            else:
                old_name = "%s-%s" % (short, dbinterface.name)
                new_name = "%s-%s" % (short, rename_to)
            fqdn_changes.extend((dns_rec.fqdn, new_name) for dns_rec
                                in addr.dns_records
                                if (dns_rec.fqdn.name == old_name and
                                    dns_rec.fqdn.dns_domain == dbdns_domain and
                                    dns_rec.fqdn != primary_fqdn))
    else:
        dbdns_domain = dbdns_env = None

    with session.no_autoflush:
        dbinterface.name = rename_to
        for dbfqdn, new_name in fqdn_changes:
            Fqdn.get_unique(session, name=new_name, dns_domain=dbdns_domain,
                            dns_environment=dbdns_env, preclude=True)
            dbfqdn.name = new_name


def check_netdev_iftype(type):
    valid_interface_types = ['oa', 'loopback', 'physical', 'virtual']
    if type not in valid_interface_types:
        raise ArgumentError("Interface type %s is not allowed for "
                            "network devices." % str(type))


def get_interfaces(dbhw_ent, interfaces, dbnetwork=None):
    ifnames = [ifname.strip().lower() for ifname in interfaces.split(",")]
    dbifaces = []
    for ifname in ifnames:
        if not ifname:
            continue
        dbinterface = first_of(dbhw_ent.interfaces,
                               lambda x, name=ifname: x.name == name)
        if not dbinterface:
            raise ArgumentError("{0} does not have an interface named "
                                "{1}.".format(dbhw_ent, ifname))
        if dbnetwork:
            dbinterface.validate_network(dbnetwork)
        dbifaces.append(dbinterface)

    if not dbifaces:
        raise ArgumentError("The interface list cannot be empty.")

    return dbifaces


def generate_mac(session, config, dbmachine):
    """ Generate a mac address for virtual hardware.

    Algorithm:

    * Query for first mac address in aqdb starting with vendor prefix,
      order by mac descending.
    * If no address, or address less than prefix start, use prefix start.
    * If the found address is not suffix end, increment by one and use it.
    * If the address is suffix end, requery for the full list and scan
      through for holes. Use the first hole.
    * If no holes, error. [In this case, we're still not completely dead
      in the water - the mac address would just need to be given manually.]

    """
    if not dbmachine.vm_container:
        raise ArgumentError("Can only automatically generate MAC "
                            "addresses for virtual hardware.")

    try:
        mac_start = MACAddress(config.get("broker", "auto_mac_start"))
    except ValueError:  # pragma: no cover
        raise AquilonError("The value of auto_mac_start in the [broker] "
                           "section is not a valid MAC address.")
    try:
        mac_end = MACAddress(config.get("broker", "auto_mac_end"))
    except ValueError:  # pragma: no cover
        raise AquilonError("The value of auto_mac_end in the [broker] "
                           "section is not a valid MAC address.")

    q = session.query(Interface.mac)
    q = q.filter(Interface.mac.between(mac_start, mac_end))
    q = q.order_by(desc(Interface.mac))

    # Prevent concurrent --automac invocations. We need a separate query for
    # the FOR UPDATE, because a blocked query won't see the value inserted
    # by the blocking query.
    session.execute(q.with_lockmode("update"))

    row = q.first()
    if not row:
        return mac_start
    highest_mac = row.mac
    if highest_mac < mac_start:
        return mac_start
    if highest_mac < mac_end:
        return highest_mac + 1

    Iface2 = aliased(Interface)
    q1 = session.query(Iface2.mac)
    q1 = q1.filter(Iface2.mac == Interface.mac + 1)

    q2 = session.query(type_coerce(Interface.mac + 1, AqMac()).label("mac"))
    q2 = q2.filter(Interface.mac.between(mac_start, mac_end - 1))
    q2 = q2.filter(~q1.exists())
    q2 = q2.order_by(Interface.mac)

    hole = q2.first()
    if hole:
        return hole.mac

    raise ArgumentError("All MAC addresses between %s and %s inclusive "
                        "are currently in use." % (mac_start, mac_end))
