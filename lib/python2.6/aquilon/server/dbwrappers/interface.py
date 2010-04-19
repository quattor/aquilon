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
"""Wrapper to make getting an interface simpler.

To an extent, this has become a dumping ground for any common ip methods.

"""

from ipaddr import IPv4Address

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import object_session
from sqlalchemy import sql

from aquilon.exceptions_ import ArgumentError, InternalError, NotFoundException
from aquilon.aqdb.column_types.aqmac import normalize_mac_address
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import (Interface, HardwareEntity, ObservedMac, System,
                                VlanInfo, ObservedVlan)
from aquilon.server.dbwrappers.system import get_system


# FIXME: interface type?  interfaces for hardware entities in general?
# FIXME: replace me with a usable get_unique
def get_interface(session, interface, machine, mac):
    q = session.query(Interface)
    errmsg = []
    if interface:
        errmsg.append("named " + interface)
        q = q.filter_by(name=interface)
    if machine:
        errmsg.append("of machine " + machine)
        q = q.join(HardwareEntity)
        q = q.filter_by(label=machine)
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

def restrict_switch_offsets(dbnetwork, ip):
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
    if dbnetwork.network.numhosts < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return

    if int(ip) - int(dbnetwork.ip) in dbnetwork.reserved_addresses:
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
            dbsystem = dbom.switch

    if ipfromsystem:
        # Assumes one system entry, not necessarily correct.
        dbsystem = get_system(session, ipfromsystem)

    if ipfromip:
        # determine network
        dbnetwork = get_net_id_from_ip(session, ipfromip)
    elif not dbnetwork:
        # Any of the other options set dbsystem...
        dbnetwork = dbsystem.network
        # Could be slightly more intelligent here, and check to see if
        # there is an IP, and then fix the network setting.
        if not dbnetwork:
            raise ArgumentError("Could not determine network to use for %s." %
                                dbsystem.fqdn)

    startip = dbnetwork.first_usable_host

    full_set = set(range(int(startip), int(dbnetwork.broadcast)))
    used_ips = session.query(System.ip).filter_by(network=dbnetwork).all()
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
    hw_type = hw.hardware_type
    if hw_type == 'machine':
        description.append("is attached to machine %s" % hw.label)
    elif hw_type == 'switch':
        if hw.switch:
            description.append("is attached to switch %s" %
                               ",".join([ts.fqdn for ts in hw.switch]))
        else:
            description.append("is attached to unnamed switch hardware")
    elif hw_type == 'chassis':
        if hw.chassis_hw:
            description.append("is attached to chassis %s" %
                               ",".join([c.fqdn for c in hw.chassis_hw]))
        else:
            description.append("is attached to unnamed chassis hardware")
    if interface.system:
        description.append("points to system %s" % interface.system.fqdn)
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
                                "no record for VLAN %s on switch %s." %
                                (vlan_id, dbswitch.fqdn))
        except MultipleResultsFound:
            raise InternalError("Too many subnets found for VLAN %s "
                                "on switch %s." %
                                (vlan_id, dbswitch.fqdn))
        if dbobserved_vlan.is_at_guest_capacity:
            raise ArgumentError("Port group %s is full for switch %s." %
                                (dbvi.port_group,
                                 dbobserved_vlan.switch.fqdn))
    elif dbmachine.host and dbmachine.host.cluster and \
         dbmachine.host.cluster.switch:
        dbswitch = dbmachine.host.cluster.switch
        q = session.query(ObservedVlan)
        q = q.filter_by(vlan_id=dbvi.vlan_id, switch=dbswitch)
        if not q.count():
            raise ArgumentError("VLAN %s not found for switch %s." %
                                (dbvi.vlan_id, dbswitch.fqdn))
    return dbvi.port_group

def choose_port_group(dbmachine):
    if dbmachine.model.machine_type != "virtual_machine":
        raise ArgumentError("Can only automatically generate "
                            "portgroup entry for virtual hardware.")
    if not dbmachine.cluster.switch:
        raise ArgumentError("Cannot automatically allocate port group: no "
                            "switch record for {0}.".format(dbmachine.cluster))
    for dbobserved_vlan in dbmachine.cluster.switch.observed_vlans:
        if dbobserved_vlan.vlan_type != 'user':
            continue
        if dbobserved_vlan.is_at_guest_capacity:
            continue
        return dbobserved_vlan.port_group
    raise ArgumentError("No available user port groups on switch %s." %
                        dbmachine.cluster.switch.fqdn)

def _type_msg(interface_type, bootable):
    if bootable is not None:
        return "%s, %s" % ("bootable" if bootable else "non-bootable",
                           interface_type)
    else:
        return interface_type

def get_or_create_interface(session, dbhw_ent, name=None, mac=None,
                            interface_type='public', bootable=None,
                            preclude=False, **extra_args):
    """ Look up an existing interface or create a new one. """

    q = session.query(Interface)
    q = q.filter_by(hardware_entity=dbhw_ent)
    # Do not filter by both name and MAC, since that would prevent discovering
    # discrepancy between the two.
    if name:
        q = q.filter_by(name=name)
    elif mac:
        q = q.filter_by(mac=mac)
    dbinterfaces = q.all()

    if preclude and dbinterfaces:
            raise ArgumentError("Interface {0!s} of {1:l} already "
                                "exists.".format(dbinterface, dbhw_ent))

    if not dbinterfaces:
        if mac:
            q = session.query(Interface)
            q = q.filter_by(mac=mac)
            dbinterface = q.first()
            if dbinterface:
                raise ArgumentError("MAC address %s is already in use: %s." %
                                    (mac, describe_interface(session,
                                                             dbinterface)))
        if not name:
            # Not enough information to create it
            raise ArgumentError("{0} has no {1} interfaces.".format(dbhw_ent,
                                                                    interface_type))
        try:
            dbinterface = Interface(name=name, hardware_entity=dbhw_ent,
                                    interface_type=interface_type, mac=mac,
                                    bootable=bootable, **extra_args)
        except ValueError, err:
            raise ArgumentError(err)
        session.add(dbinterface)
        session.flush()
        session.refresh(dbinterface)
    elif len(dbinterfaces) == 1:
        dbinterface = dbinterfaces[0]
        # The user input must be normalized before comparing it with a value
        # from the DB
        if mac and dbinterface.mac != normalize_mac_address(mac):
            raise ArgumentError("Interface {0!s} of {1:l} exists, but has MAC "
                                "address {2} instead of "
                                "{3}.".format(dbinterface, dbhw_ent,
                                              dbinterface.mac, mac))
        if interface_type and dbinterface.interface_type != interface_type:
            raise ArgumentError("Interface {0!s} of {1:l} is of type {2}, not "
                                "{3}.".format(dbinterface, dbhw_ent,
                                              dbinterface.interface_type,
                                              interface_type))
    else:
        # Since both the MAC and name are unique keys, we can arrive here only
        # if neither of them were specified. Try to match the interface based on
        # type and boot settings.
        dbinterface = None
        for iface in dbinterfaces:
            if iface.interface_type != interface_type:
                continue
            if bootable is not None and iface.bootable != bootable:
                continue
            if dbinterface:
                type_msg = _type_msg(interface_type, bootable)
                raise ArgumentError("{0} has multiple {1} interfaces, please "
                                    "specify which one to "
                                    "use.".format(dbhw_ent, type_msg))
            dbinterface = iface
        if not dbinterface:
            type_msg = _type_msg(interface_type, bootable)
            raise NotFoundException("{0} has no {1} interfaces "
                                    "defined.".format(dbhw_ent, type_msg))
    return dbinterface
