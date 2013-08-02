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
"""Wrapper to make getting an interface simpler.

To an extent, this has become a dumping ground for any common ip methods.

"""

from ipaddr import IPv4Address
import re

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import object_session

from aquilon.exceptions_ import ArgumentError, InternalError
from aquilon.aqdb.model import (Interface, ObservedMac, Fqdn, ARecord, VlanInfo,
                                ObservedVlan, Network, AddressAssignment, Model,
                                Bunker, Location, HardwareEntity)
from aquilon.aqdb.model.network import get_net_id_from_ip


_vlan_re = re.compile(r'^(.*)\.(\d+)$')


def check_ip_restrictions(dbnetwork, ip, relaxed=False):
    """ given a network and ip addr, raise an exception if the ip is reserved

        Used during ip assignment as a check against grabbing an ip address
        that we have reserved as a dynamic dhcp pool for switches (and
        potentially other assorted devices) The remainder of addresses are to
        be used for static assignment (for telco gear only).

        Setting relaxed to true means checking only the most obvious problems.
    """

    #TODO: if the network type doesn't have any applicable offsets, we
    #      probably want to reserve the first ip for the gateway on all networks
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


def generate_ip(session, logger, dbinterface, ip=None, ipfromip=None,
                ipfromsystem=None, autoip=None, ipalgorithm=None, compel=False,
                network_environment=None, audit_results=None, **kwargs):
    ip_options = [ip, ipfromip, ipfromsystem, autoip]
    numopts = sum([1 if opt else 0 for opt in ip_options])
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

    dbsystem = None
    dbnetwork = None
    if autoip:
        if not dbinterface:
            raise ArgumentError("No interface available to automatically "
                                "generate an IP address.")
        if dbinterface.port_group:
            # This could either be an interface from a virtual machine
            # or an interface on an ESX vmhost.
            dbcluster = None
            if getattr(dbinterface.hardware_entity, "cluster", None):
                # VM
                dbcluster = dbinterface.hardware_entity.cluster
            elif getattr(dbinterface.hardware_entity, "host", None):
                dbcluster = dbinterface.hardware_entity.host.cluster
            if not dbcluster:
                raise ArgumentError("Can only automatically assign an IP "
                                    "address to an interface with a port "
                                    "group on virtual machines or ESX hosts.")
            if not dbcluster.switch:
                raise ArgumentError("Cannot automatically assign an IP "
                                    "address to an interface with a port group "
                                    "since {0} is not associated with a "
                                    "switch.".format(dbcluster))
            vlan_id = VlanInfo.get_vlan_id(session, dbinterface.port_group)
            dbnetwork = ObservedVlan.get_network(session, vlan_id=vlan_id,
                                                 switch=dbcluster.switch,
                                                 compel=ArgumentError)
        elif dbinterface.mac:
            q = session.query(ObservedMac)
            q = q.filter_by(mac_address=dbinterface.mac)
            q = q.order_by(desc(ObservedMac.last_seen))
            dbom = q.first()
            if not dbom:
                raise ArgumentError("No switch found in the discovery table "
                                    "for MAC address %s." % dbinterface.mac)
            if not dbom.switch.primary_ip:
                raise ArgumentError("{0} does not have a primary IP address "
                                    "to use for network "
                                    "selection.".format(dbom.switch))
            dbnetwork = get_net_id_from_ip(session, dbom.switch.primary_ip)
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

    if not dbnetwork:
        raise ArgumentError("Could not determine network to use for %s." %
                            dbsystem.fqdn)

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
    used_set = set([int(item.ip) for item in used_ips])
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
            logger.info("Selected IP address {0!s} for {1:l}"
                        .format(ip, dbinterface))
        else:
            logger.info("Selected IP address %s" % ip)
        audit_results.append(('ip', ip))

    return ip


def describe_interface(session, interface):
    description = ["%s interface %s has MAC address %s and boot=%s" %
                   (interface.interface_type, interface.name, interface.mac,
                    interface.bootable)]
    hw = interface.hardware_entity
    description.append("is attached to {0:l}".format(hw))
    for addr in interface.assignments:
        for dns_rec in addr.dns_records:
            if addr.label:
                description.append("has address {0:a} label "
                                   "{1}".format(dns_rec, addr.label))
            else:
                description.append("has address {0:a}".format(dns_rec))
    ifaces = session.query(Interface).filter_by(mac=interface.mac).all()
    if len(ifaces) == 1 and ifaces[0] != interface:
        description.append("but MAC address %s is in use by %s" %
                           (interface.mac, format(ifaces[0].hardware_entity)))
    return ", ".join(description)


def verify_port_group(dbmachine, port_group):
    """Validate that the port_group can be used on an interface.

    If the machine is virtual, check that the corresponding VLAN has
    been observed on the cluster's switch.

    If the machine is physical but is part of an ESX cluster, also
    check that the VLAN has been observed.

    Otherwise just accept the label.

    As a convenience, return None (unset the port_group) if an empty
    string is passed in.

    """
    if not port_group:
        return None
    session = object_session(dbmachine)
    dbvi = VlanInfo.get_unique(session, port_group=port_group, compel=True)
    if dbmachine.model.machine_type == "virtual_machine":
        dbswitch = dbmachine.cluster.switch
        if not dbswitch:
            raise ArgumentError("Cannot verify port group availability: no "
                                "switch record for {0}.".format(dbmachine.cluster))
        q = session.query(ObservedVlan)
        q = q.filter_by(vlan_id=dbvi.vlan_id)
        q = q.filter_by(switch=dbswitch)
        try:
            dbobserved_vlan = q.one()
        except NoResultFound:
            raise ArgumentError("Cannot verify port group availability: "
                                "no record for VLAN {0} on "
                                "{1:l}.".format(dbvi.vlan_id, dbswitch))
        except MultipleResultsFound:  # pragma: no cover
            raise InternalError("Too many subnets found for VLAN {0} "
                                "on {1:l}.".format(dbvi.vlan_id, dbswitch))
        if dbobserved_vlan.network.is_at_guest_capacity:
            raise ArgumentError("Port group {0} is full for "
                                "{1:l}.".format(dbvi.port_group,
                                                dbobserved_vlan.switch))
    elif dbmachine.host and dbmachine.host.cluster and \
         dbmachine.host.cluster.switch:
        dbswitch = dbmachine.host.cluster.switch
        q = session.query(ObservedVlan)
        q = q.filter_by(vlan_id=dbvi.vlan_id, switch=dbswitch)
        if not q.count():
            raise ArgumentError("VLAN {0} not found for "
                                "{1:l}.".format(dbvi.vlan_id, dbswitch))
    return dbvi.port_group


def choose_port_group(session, logger, dbmachine):
    if dbmachine.model.machine_type != "virtual_machine":
        raise ArgumentError("Can only automatically generate "
                            "portgroup entry for virtual hardware.")
    if not dbmachine.cluster.switch:
        raise ArgumentError("Cannot automatically allocate port group: no "
                            "switch record for {0}.".format(dbmachine.cluster))

    selected_vlan = None

    sw = dbmachine.cluster.switch

    # filter for user vlans only
    networks = session.query(Network).\
            join("observed_vlans", "vlan").\
            filter(VlanInfo.vlan_type == "user").\
            filter(ObservedVlan.switch == sw).\
            order_by(VlanInfo.vlan_id).all()

    # then filter by capacity
    networks = [nw for nw in networks
                   if not nw.is_at_guest_capacity]

    for dbobserved_vlan in [vlan for n in networks
                 for vlan in n.observed_vlans if vlan.vlan_type == "user"]:
        if not selected_vlan or \
           selected_vlan.guest_count > dbobserved_vlan.guest_count:
            selected_vlan = dbobserved_vlan

    if selected_vlan:
        logger.info("Selected port group {0} for {1:l} (based on {2:l})"
                    .format(selected_vlan.port_group, dbmachine, sw))
        return selected_vlan.port_group
    raise ArgumentError("No available user port groups on "
                        "{0:l}.".format(dbmachine.cluster.switch))


def _type_msg(interface_type, bootable):
    if bootable is not None:
        return "%s, %s" % ("bootable" if bootable else "non-bootable",
                           interface_type)
    else:
        return interface_type


def get_or_create_interface(session, dbhw_ent, name=None, mac=None,
                            model=None, vendor=None,
                            interface_type='public', bootable=None,
                            preclude=False, port_group=None, comments=None):
    """
    Look up an existing interface or create a new one.

    If either the name or the MAC address is given and a matching interface
    exists, then that interface is returned and the other parameters are not
    checked.

    If neither the name nor the MAC address is given, but there is just one
    existing interface matching the specified interface_type/bootable/port_group
    combination, then that interface is returned. If there are multiple matches,
    an exception is raised.

    If no interfaces were found, and enough parameters are provided, then a new
    interface is created. For this purpose, at least the name and in some cases
    the MAC address must be specified.

    Setting preclude to True enforces the creation of a new interface. An error
    is raised if a conflicting interface already exists.
    """

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
            raise ArgumentError("MAC address %s is already in use: %s." %
                                (mac, describe_interface(session,
                                                         dbinterface)))

    if name and not dbinterface:
        # Special logic to allow "add_interface" to succeed if there is an
        # auto-created interface already
        if preclude and len(dbhw_ent.interfaces) == 1:
            dbinterface = dbhw_ent.interfaces[0]
            if dbinterface.mac is None and \
               dbinterface.interface_type == interface_type and \
               dbinterface.comments is not None and \
               dbinterface.comments.startswith("Created automatically"):
                dbinterface.name = name
                dbinterface.mac = mac
                if hasattr(dbinterface, "bootable") and bootable is not None:
                    dbinterface.bootable = bootable
                dbinterface.comments = comments
                if hasattr(dbinterface, "port_group"):
                    dbinterface.port_group = port_group
                session.flush()
                return dbinterface

        dbinterface = None
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
            if port_group is not None and (not hasattr(iface, "port_group") or
                                           iface.port_group != port_group):
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
    if port_group is not None:
        extra_args["port_group"] = port_group

    if not model and not vendor:
        dbmodel = dbhw_ent.model.nic_model
    elif not cls.model_allowed:
        raise ArgumentError("Model/vendor can not be set for a %s." %
                            cls._get_class_label(tolower=True))
    else:
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   machine_type="nic", compel=True)

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

    for key in extra_args.keys():
        if key not in cls.extra_fields:
            raise InternalError("Parameter %s is not valid for %s "
                                "interfaces." % (key, interface_type))

    try:
        dbinterface = cls(name=name, mac=mac, comments=comments, model=dbmodel,
                          default_route=default_route, **extra_args)
    except ValueError, err:
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
        logger.warn("Bunker violation: {0:l} is inside {1:l}, but {2:l} is "
                    "not bunkerized.".format(dbrack, rack_bunker, dbnetwork))
        return

    session = object_session(dbrack)

    if dbnetwork.may_span_buildings and "." in net_bunker.name:
        # If a network spans buildings, we pretend it's in the bunker local to
        # the rack's building, even if it was registered to the other side. This
        # hack could be removed if we had buckets as a Location subclass.
        bucket, building = net_bunker.name.split(".", 1)
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
            logger.warn("Bunker violation: {0:l} is inside {1:l}, but {2:l} "
                        "is not inside a bunker."
                        .format(dbnetwork, net_bunker, dbrack))
            return

        logger.client_info("Moving {0:l} into {1:l} based on network tagging."
                           .format(dbrack, expected_bunker))
        dbrack.update_parent(parent=expected_bunker)
        rack_bunker = expected_bunker

    if rack_bunker != expected_bunker:
        logger.warn("Bunker violation: {0:l} is inside {1:l}, but "
                    "{2:l} is inside {3:l}."
                    .format(dbrack, rack_bunker, dbnetwork, expected_bunker))


def assign_address(dbinterface, ip, dbnetwork, label=None, resource=None,
                   logger=None):
    assert isinstance(dbinterface, Interface)

    dns_environment = dbnetwork.network_environment.dns_environment

    if dbinterface.master:
        raise ArgumentError("Slave interfaces cannot hold addresses.")

    dbrack = dbinterface.hardware_entity.location.rack
    if dbrack:
        enforce_bucket_alignment(dbrack, dbnetwork, logger)

    for addr in dbinterface.assignments:
        if not label and not addr.label:
            raise ArgumentError("{0} already has an IP "
                                "address.".format(dbinterface))
        if label and addr.label == label:
            raise ArgumentError("{0} already has an alias named "
                                "{1}.".format(dbinterface, label))
        if addr.network.network_environment != dbnetwork.network_environment:
            raise ArgumentError("{0} already has an IP address from "
                                "{1:l}.  Network environments cannot be "
                                "mixed.".format(dbinterface,
                                                addr.network.network_environment))
        if addr.ip == ip:
            raise ArgumentError("{0} already has IP address {1} "
                                "configured.".format(dbinterface, ip))

    dbinterface.assignments.append(AddressAssignment(ip=ip, network=dbnetwork,
                                                     label=label,
                                                     service_address=resource,
                                                     dns_environment=dns_environment))


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
            fqdn_changes.extend([(dns_rec.fqdn, new_name) for dns_rec
                                 in addr.dns_records
                                 if dns_rec.fqdn.name == old_name and
                                    dns_rec.fqdn.dns_domain == dbdns_domain and
                                    dns_rec.fqdn != primary_fqdn])
    else:
        dbdns_domain = dbdns_env = None

    with session.no_autoflush:
        dbinterface.name = rename_to
        for dbfqdn, new_name in fqdn_changes:
            Fqdn.get_unique(session, name=new_name, dns_domain=dbdns_domain,
                            dns_environment=dbdns_env, preclude=True)
            dbfqdn.name = new_name
