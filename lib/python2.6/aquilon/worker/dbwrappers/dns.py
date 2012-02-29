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
""" Helpers for managing DNS-related objects """

from sqlalchemy.orm import object_session

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Fqdn, DnsRecord, ARecord, DynamicStub,
                                AddressAssignment, NetworkEnvironment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.interface import check_ip_restrictions


def delete_dns_record(dbdns_rec):
    """
    Delete a DNS record 

    Deleting a DNS record is a bit tricky because we do not want to keep
    orphaned FQDN entries.
    """

    session = object_session(dbdns_rec)

    if dbdns_rec.aliases:
        raise ArgumentError("{0} still has aliases, delete them "
                            "first.".format(dbdns_rec))
    if dbdns_rec.srv_records:
        raise ArgumentError("{0} is still in use by SRV records, delete them "
                            "first.".format(dbdns_rec))

    # Lock the FQDN
    dbfqdn = dbdns_rec.fqdn
    dbfqdn.lock_row()

    # Delete the DNS record
    session.delete(dbdns_rec)
    session.flush()

    # Delete the FQDN if it is orphaned
    q = session.query(DnsRecord)
    q = q.filter_by(fqdn_id=dbfqdn.id)
    if q.count() == 0:
        session.delete(dbfqdn)
    else:
        session.expire(dbfqdn, ['dns_records'])

def convert_reserved_to_arecord(session, dbdns_rec, dbnetwork, ip):
    comments = dbdns_rec.comments
    dbhw_ent = dbdns_rec.hardware_entity
    dbfqdn = dbdns_rec.fqdn

    session.delete(dbdns_rec)
    session.flush()
    session.expire(dbhw_ent, ['primary_name'])
    session.expire(dbfqdn, ['dns_records'])
    dbdns_rec = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork,
                        comments=comments)
    session.add(dbdns_rec)
    if dbhw_ent:
        dbhw_ent.primary_name = dbdns_rec

    return dbdns_rec

def grab_address(session, fqdn, ip, network_environment=None,
                 usage='system', relaxed=False):
    dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                         network_environment)

    dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
    check_ip_restrictions(dbnetwork, ip, relaxed=relaxed)

    delete_old_dsdb_entry = False
    dbfqdn = Fqdn.get_or_create(session, fqdn=fqdn,
                                dns_environment=dbnet_env.dns_environment)
    if dbfqdn.dns_domain.restricted:
        raise ArgumentError("{0} is restricted, auxiliary addresses "
                            "are not allowed.".format(dbfqdn.dns_domain))
    if ip:
        # TODO: move this check to the model
        q = session.query(DynamicStub)
        q = q.filter_by(network=dbnetwork)
        q = q.filter_by(ip=ip)
        dbdns_rec = q.first()
        if dbdns_rec:
            raise ArgumentError("Address {0:a} is reserved for dynamic "
                                "DHCP.".format(dbdns_rec))

        dbdns_rec = ARecord.get_unique(session, fqdn=dbfqdn, ip=ip,
                                       network=dbnetwork)
        if dbdns_rec:
            # If it was just a pure DNS placeholder, then delete & re-add it
            if not dbdns_rec.assignments:
                delete_old_dsdb_entry = True
        else:
            dbdns_rec = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork)
            session.add(dbdns_rec)
    else:
        dbdns_rec = ARecord.get_unique(session, fqdn=dbfqdn, compel=True)
        if isinstance(dbdns_rec, DynamicStub):
            raise ArgumentError("Address {0:a} is reserved for dynamic "
                                "DHCP.".format(dbdns_rec))
        ip = dbdns_rec.ip
        dbnetwork = dbdns_rec.network

        if dbnetwork.network_environment != dbnet_env:
            raise ArgumentError("Address {0:a} lives in {1:l}, not in "
                                "{2:l}.  Use the --network_environment "
                                "option to select the correct environment."
                                .format(dbdns_rec,
                                        dbnetwork.network_environment,
                                        dbnet_env))

        # If it was just a pure DNS placeholder, then delete & re-add it
        if not dbdns_rec.assignments:
            delete_old_dsdb_entry = True

    # Sanity checks
    if dbdns_rec.hardware_entity:
        raise ArgumentError("Address {0:a} is already used as a primary name."
                            .format(dbdns_rec))

    q = session.query(AddressAssignment)
    q = q.filter_by(network=dbnetwork)
    q = q.filter_by(ip=ip)
    other_uses = q.all()
    if usage == "system":
        if other_uses:
            raise ArgumentError("IP address {0} is already in use. Non-zebra "
                                "addresses cannot be assigned to multiple "
                                "machines/interfaces.".format(ip))
    elif usage == "zebra":
        for addr in other_uses:
            if addr.usage != "zebra":
                raise ArgumentError("IP address {0} is already used by {1:l} "
                                    "and is not configured for "
                                    "Zebra.".format(ip, addr.interface))

    return dbdns_rec, delete_old_dsdb_entry
