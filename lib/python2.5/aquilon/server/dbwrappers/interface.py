# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

from twisted.python import log
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.sql.expression import asc, desc

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types.IPV4 import dq_to_int
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import (Interface, Machine, ObservedMac, TorSwitch,
                                 System)
from aquilon.server.dbwrappers.system import get_system


# FIXME: interface type?  interfaces for hardware entities in general?
def get_interface(session, interface, machine, mac, ip):
    q = session.query(Interface)
    if machine:
        q = q.filter(Interface.hardware_entity_id==Machine.machine_id)
        q = q.filter(Machine.name==machine)
    if interface:
        q = q.filter_by(name=interface)
    if mac:
        q = q.filter_by(mac=mac)
    if ip:
        q = q.filter_by(ip=ip)
        pass

    try:
        dbinterface = q.one()
    except InvalidRequestError, e:
        raise ArgumentError("Interface not found, make sure it has been specified uniquely: %s" % e)
    return dbinterface

def restrict_tor_offsets(session, dbnetwork, ip):
    if ip is None:
        # Simple passthrough to make calling logic easier.
        return
    if dbnetwork.mask < 8:
        # This network doesn't have enough addresses, the test is irrelevant.
        return
    dbtor_switch = session.query(TorSwitch).filter_by(network=dbnetwork).first()
    if not dbtor_switch:
        return
    netip = dq_to_int(dbnetwork.ip)
    thisip = dq_to_int(ip)
    if thisip == (netip + 6) or thisip == (netip + 7):
        raise ArgumentError("The IP address %s is reserved for dynamic dhcp on subnet %s by tor_switch %s." %
                (ip, dbnetwork.ip, dbtor_switch.fqdn))

def generate_ip(session, dbinterface, ip=None, ipfromip=None,
                ipfromsystem=None, autoip=None, ipalgorithm=None,
                **kwargs):
    if not (ip or ipfromip or ipfromsystem or autoip):
        return None
    if ip:
        if ipfromip:
            raise ArgumentError("Cannot specify both --ip and --ipfromip")
        if ipfromsystem:
            raise ArgumentError("Cannot specify both --ip and --ipfromsystem")
        if autoip:
            raise ArgumentError("Cannot specify both --ip and --autoip")
        return ip
    dbsystem = None
    if autoip:
        if ipfromip:
            raise ArgumentError("Cannot specify both --autoip and --ipfromip")
        if ipfromsystem:
            raise ArgumentError("Cannot specify both --autoip and "
                                "--ipfromsystem")
        q = session.query(ObservedMac)
        q = q.filter_by(mac_address=dbinterface.mac)
        q = q.order_by(desc(ObservedMac.last_seen))
        dbsystem = q.first()
        if not dbsystem:
            raise ArgumentError("No switch found in the discovery table for mac %s" % dbinterface.mac)
    if ipfromsystem:
        if ipfromip:
            raise ArgumentError("Cannot specify both --ipfromsystem and "
                                "--ipfromip")
        # Assumes one system entry, not necessarily correct.
        dbsystem = get_system(session, ipfromsystem)
    if ipfromip:
        # determine network
        dbnetwork = get_net_id_from_ip(session, ipfromip)
    else:
        # Any of the other options set dbsystem...
        dbnetwork = dbsystem.network
        # Could be slightly more intelligent here, and check to see if
        # there is an IP, and then fix the network setting.
        if not dbnetwork:
            raise ArgumentError("Could not determine network to use for"
                                "%s" % dbsystem.fqdn)
    start = 2
    if dbnetwork.network_type == 'tor_net' or \
       session.query(TorSwitch).filter_by(network=dbnetwork).first():
       #(dbsystem and isinstance(dbsystem, TorSwitch)):
        start = 8
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
