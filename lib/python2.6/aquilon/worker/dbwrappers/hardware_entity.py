# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import (HardwareEntity, Model, ReservedName,
                                AddressAssignment, Interface, Vendor)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.dns import convert_reserved_to_arecord
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (check_ip_restrictions,
                                                 assign_address)
from aquilon.utils import first_of


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

def update_primary_ip(session, dbhw_ent, ip):
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

        assign_address(dbinterface, ip, dbnetwork)
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
