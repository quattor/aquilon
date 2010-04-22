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


from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import object_session

from aquilon.exceptions_ import ArgumentError, InternalError, NotFoundException
from aquilon.aqdb.column_types.IPV4 import dq_to_int
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import (Interface, Machine, ObservedMac, System,
                                VlanInfo, ObservedVlan)
from aquilon.server.dbwrappers.system import get_system


# FIXME: interface type?  interfaces for hardware entities in general?
def get_interface(session, interface, machine, mac):
    q = session.query(Interface)
    errmsg = []
    if interface:
        errmsg.append("named " + interface)
        q = q.filter_by(name=interface)
    if machine:
        errmsg.append("of machine " + machine)
        q = q.filter(Interface.hardware_entity_id==Machine.machine_id)
        q = q.filter(Machine.name==machine)
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

def restrict_tor_offsets(dbnetwork, ip):
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return
    if dbnetwork.mask < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return

    if dbnetwork.network_type == 'tor_net':
        offsets = [6, 7]
    elif dbnetwork.network_type == 'tor_net2':
        offsets = [7, 8]
    else:
        return

    netip = dq_to_int(dbnetwork.ip)
    thisip = dq_to_int(ip)

    for offset in offsets:
        if thisip == netip + offset:
            raise ArgumentError("The IP address %s is reserved for dynamic "
                                "dhcp for a tor_switch on subnet %s" %
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
                                "generate an IP.")
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
                raise ArgumentError("Can only automatically assign an IP to "
                                    "an interface with a port group on "
                                    "virtual machines or ESX hosts.")
            if not dbcluster.switch:
                raise ArgumentError("Cannot automatically assign an IP to "
                                    "an interface with a port group since "
                                    "cluster %s is not associated with a "
                                    "switch" % dbcluster.switch)
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
                                    "for mac %s" % dbinterface.mac)
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
            raise ArgumentError("Could not determine network to use for"
                                "%s" % dbsystem.fqdn)

    if dbnetwork.network_type == 'tor_net':
        start = 8
    elif dbnetwork.network_type == 'tor_net2':
        start = 9
    elif dbnetwork.network_type == 'vm_storage_net':
        start = 40
    else:
        start = 5
    # Not sure what to do about networks like /32 and /31...
    if dbnetwork.mask < start:
        start = 0

    pool = dbnetwork.addresses()
    if ipalgorithm is None or ipalgorithm == 'lowest':
        for ip in pool[start:]:
            # Might be more efficient to query for all Systems with dbnetwork
            # ordered by IP, and increment up both lists.
            if session.query(System).filter_by(ip=ip).first():
                continue
            return ip
        raise ArgumentError("No available IP found on network %s" %
                            dbnetwork.ip)
    elif ipalgorithm == 'max':
        # Find the highest IP defined in the subnet, and add one.
        q = session.query(System)
        q = q.filter_by(network=dbnetwork)
        q = q.order_by(desc(System.ip))
        first = q.first()
        if not first:
            return pool[start]
        i = pool.index(first.ip)
        if i < start:
            return pool[start]
        if (i + 1) >= len(pool):
            raise ArgumentError("No remaining IPs found on network %s.  "
                                "%s [%s] has the highest address." %
                                (dbnetwork.ip, first.fqdn, first.ip))
        return pool[i + 1]
    raise ArgumentError("Unknown algorithm '%s'" % ipalgorithm)

def describe_interface(session, interface):
    description = ["%s interface %s has mac %s and boot=%s" %
                   (interface.interface_type, interface.name, interface.mac,
                    interface.bootable)]
    hw = interface.hardware_entity
    hw_type = hw.hardware_entity_type
    if hw_type == 'machine':
        description.append("is attached to machine %s" % hw.name)
    elif hw_type == 'tor_switch_hw':
        if hw.tor_switch:
            description.append("is attached to tor_switch %s" %
                               ",".join([ts.fqdn for ts in hw.tor_switch]))
        else:
            description.append("is attached to unnamed tor_switch hardware")
    elif hw_type == 'chassis_hw':
        if hw.chassis_hw:
            description.append("is attached to chassis %s" %
                               ",".join([c.fqdn for c in hw.chassis_hw]))
        else:
            description.append("is attached to unnamed chassis hardware")
    elif getattr(hw, "name", None):
        description.append("is attached to %s %s" % (hw_type, hw.name))
    if interface.system:
        description.append("points to system %s" % interface.system.fqdn)
    systems = session.query(System).filter_by(mac=interface.mac).all()
    if len(systems) == 1 and systems[0] != interface.system:
        description.append("but mac is in use by '%s'" % systems[0].fqdn)
    if len(systems) > 1:
        description.append("and mac is in use by '%s'" %
                           ",".join([s.fqdn for s in systems]))
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
            raise ArgumentError("Cannot verify port group availability: "
                                "no tor_switch record for cluster %s" %
                                dbmachine.cluster)
        q = session.query(ObservedVlan)
        q = q.filter_by(vlan_id=dbvi.vlan_id)
        q = q.filter_by(switch=dbswitch)
        try:
            dbobserved_vlan = q.one()
        except NoResultFound:
            raise ArgumentError("Cannot verify port group availability: "
                                "no record for VLAN %s on switch %s" %
                                (vlan_id, dbswitch.fqdn))
        except MultipleResultsFound:
            raise InternalError("Too many subnets found for VLAN %s "
                                "on switch %s" %
                                (vlan_id, dbswitch.fqdn))
        if dbobserved_vlan.is_at_guest_capacity:
            raise ArgumentError("Port group %s is full for switch %s" %
                                (dbvi.port_group,
                                 dbobserved_vlan.switch.fqdn))
    elif dbmachine.host and dbmachine.host.cluster and \
         dbmachine.host.cluster.switch:
        dbswitch = dbmachine.host.cluster.switch
        q = session.query(ObservedVlan)
        q = q.filter_by(vlan_id=dbvi.vlan_id, switch=dbswitch)
        if not q.count():
            raise ArgumentError("VLAN %s not found for switch %s" %
                                (dbvi.vlan_id, dbswitch.fqdn))
    return dbvi.port_group

def choose_port_group(dbmachine):
    if dbmachine.model.machine_type != "virtual_machine":
        raise ArgumentError("Can only automatically generate "
                            "portgroup entry for virtual hardware.")
    if not dbmachine.cluster.switch:
        raise ArgumentError("Cannot automatically allocate port group:"
                            " no tor_switch record for cluster %s" %
                            dbmachine.cluster)
    for dbobserved_vlan in dbmachine.cluster.switch.observed_vlans:
        if dbobserved_vlan.vlan_type != 'user':
            continue
        if dbobserved_vlan.is_at_guest_capacity:
            continue
        return dbobserved_vlan.port_group
    raise ArgumentError("No available user port groups on switch %s" %
                        dbmachine.cluster.switch.fqdn)
