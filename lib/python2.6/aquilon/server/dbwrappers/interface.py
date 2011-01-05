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
"""Wrapper to make getting an interface simpler.

To an extent, this has become a dumping ground for any common ip methods.

"""

from ipaddr import IPv4Address
import re

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import object_session
from sqlalchemy.sql import select

from aquilon.exceptions_ import ArgumentError, InternalError, NotFoundException
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import (Interface, HardwareEntity, ObservedMac,
                                FutureARecord, VlanInfo, ObservedVlan, Network)
from aquilon.server.dbwrappers.system import get_system
from aquilon.utils import force_mac


_vlan_re = re.compile(r'^(.*)\.(\d+)$')


# FIXME: interface type?
# FIXME: replace me with a usable get_unique
def get_interface(session, interface, dbhw_ent, mac):
    q = session.query(Interface)
    errmsg = []
    if interface:
        errmsg.append("named " + interface)
        q = q.filter_by(name=interface)
    if dbhw_ent:
        errmsg.append("of {0:l} ".format(dbhw_ent))
        q = q.join(HardwareEntity)
        q = q.filter(HardwareEntity.id == dbhw_ent.id)
        q = q.reset_joinpoint()
    if mac:
        errmsg.append("having MAC address " + mac)
        q = q.filter_by(mac=mac)

    try:
        dbinterface = q.one()
    except NoResultFound:
        raise NotFoundException("Interface %s not found." % " ".join(errmsg))
    except MultipleResultsFound:
        raise ArgumentError("There are multiple interfaces %s." %
                            " ".join(errmsg))
    return dbinterface

def check_ip_restrictions(dbnetwork, ip):
    """ given a network and ip addr, raise an exception if the ip is reserved

        Used during ip assignment as a check against grabbing an ip address
        that we have reserved as a dynamic dhcp pool for switches (and
        potentially other assorted devices) The remainder of addresses are to
        be used for static assignment (for telco gear only).
    """

    #TODO: if the network type doesn't have any applicable offsets, we
    #      probably want to reserve the first ip for the gateway on all networks
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return

    if ip < dbnetwork.ip or ip > dbnetwork.broadcast:  # pragma: no cover
        raise InternalError("IP address {0!s} is outside "
                            "{1:l}.".format(ip, dbnetwork))
    if ip == dbnetwork.ip:
        raise ArgumentError("IP address %s is the address of network %s." %
                            (ip, dbnetwork.name))
    if ip == dbnetwork.broadcast:
        raise ArgumentError("IP address %s is the broadcast address of "
                            "network %s." % (ip, dbnetwork.name))

    if dbnetwork.network.numhosts < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return

    if int(ip) - int(dbnetwork.ip) in dbnetwork.reserved_offsets:
        raise ArgumentError("The IP address %s is reserved for dynamic "
                            "DHCP for a switch on subnet %s." %
                            (ip, dbnetwork.ip))
    return

def generate_ip(session, dbinterface, ip=None, ipfromip=None,
                ipfromsystem=None, autoip=None, ipalgorithm=None,
                compel=False, **kwargs):
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
        else:
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

    if ipfromsystem:
        # Assumes one system entry, not necessarily correct.
        dbsystem = get_system(session, ipfromsystem)
        if hasattr(dbsystem, "ip"):
            dbnetwork = get_net_id_from_ip(session, dbsystem.ip)

    if ipfromip:
        # determine network
        dbnetwork = get_net_id_from_ip(session, ipfromip)

    if not dbnetwork:
        raise ArgumentError("Could not determine network to use for %s." %
                            dbsystem.fqdn)

    # When there are e.g. multiple "add manager --autoip" operations going on in
    # parallel, we must ensure that they won't try to use the same IP address.
    # This query places a database lock on the network, which means IP address
    # generation within a network will be serialized, while operations on
    # different networks can still run in parallel. The lock will be released by
    # COMMIT or ROLLBACK.
    session.execute(select([Network.id], Network.id == dbnetwork.id,
                           for_update=True)).fetchall()

    startip = dbnetwork.first_usable_host

    used_ips = session.query(FutureARecord.ip)
    used_ips = used_ips.filter(FutureARecord.ip >= startip)
    used_ips = used_ips.filter(FutureARecord.ip < dbnetwork.broadcast)

    full_set = set(range(int(startip), int(dbnetwork.broadcast)))
    used_set = set([int(item.ip) for item in used_ips])
    free_set = full_set - used_set

    if not free_set:
        raise ArgumentError("No available IP addresses found on "
                            "network %s." % str(dbnetwork.network))

    if ipalgorithm is None or ipalgorithm == 'lowest':
        # Select the lowest available address
        ip = IPv4Address(min(free_set))
        return ip
    elif ipalgorithm == 'highest':
        # Select the highest available address
        ip = IPv4Address(max(free_set))
        return ip
    elif ipalgorithm == 'max':
        # Return the max. used address + 1
        if not used_set:
            #Avoids ValueError being thrown when used_set is empty
            return IPv4Address(min(free_set))
        ip = None
        next = max(used_set)
        if not next + 1 in free_set:
            raise ArgumentError("Failed to find an IP that is suitable for " \
                                "--ipalgorithm=max.  Try an other algorithm "
                                "as there are still some free addresses.")
        ip = IPv4Address(next + 1)
        return ip
    raise ArgumentError("Unknown algorithm %s." % ipalgorithm)

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
                                "{1:l}.".format(vlan_id, dbswitch))
        except MultipleResultsFound:
            raise InternalError("Too many subnets found for VLAN {0} "
                                "on {1:l}.".format(vlan_id, dbswitch))
        if dbobserved_vlan.is_at_guest_capacity:
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

def choose_port_group(dbmachine):
    if dbmachine.model.machine_type != "virtual_machine":
        raise ArgumentError("Can only automatically generate "
                            "portgroup entry for virtual hardware.")
    if not dbmachine.cluster.switch:
        raise ArgumentError("Cannot automatically allocate port group: no "
                            "switch record for {0}.".format(dbmachine.cluster))
    selected_vlan = None
    for dbobserved_vlan in dbmachine.cluster.switch.observed_vlans:
        if dbobserved_vlan.vlan_type != 'user':
            continue
        if dbobserved_vlan.is_at_guest_capacity:
            continue
        if not selected_vlan or \
           selected_vlan.guest_count > dbobserved_vlan.guest_count:
            selected_vlan = dbobserved_vlan
    if selected_vlan:
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

    cls = None
    try:
        cls = Interface.__mapper__.polymorphic_map[interface_type].class_
    except KeyError:
        raise ArgumentError("Invalid interface type '%s'." % interface_type)

    extra_args = {}
    if bootable is not None:
        extra_args["bootable"] = bootable
    if port_group is not None:
        extra_args["port_group"] = port_group

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
            raise ArgumentError("Parameter %s is not valid for %s "
                                "interfaces." % (key, interface_type))

    try:
        dbinterface = cls(name=name, mac=mac, comments=comments,
                          **extra_args)
    except ValueError, err:
        raise ArgumentError(err)

    dbhw_ent.interfaces.append(dbinterface)
    session.flush()
    return dbinterface
