# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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

from sqlalchemy.orm import object_session, joinedload

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import (Fqdn, DnsRecord, ARecord, DynamicStub,
                                ReservedName, DnsEnvironment,
                                AddressAssignment, NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
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

def _check_netenv_compat(dbdns_rec, dbnet_env):
    """ Verify that a DNS record is consistent with a network environment """
    dbnetwork = dbdns_rec.network
    if dbnetwork.network_environment != dbnet_env:
        raise ArgumentError("Address {0:a} lives in {1:l}, not in {2:l}.  Use "
                            "the --network_environment option to select the "
                            "correct environment."
                            .format(dbdns_rec, dbnetwork.network_environment,
                                    dbnet_env))

def _forbid_dyndns(dbdns_rec):
    """ Raise an error if the address is reserved for dynamic DHCP """
    if isinstance(dbdns_rec, DynamicStub):
            raise ArgumentError("Address {0:a} is reserved for dynamic "
                            "DHCP.".format(dbdns_rec))

#
# Locking rules:
# - Locking the DNS domain ensures exclusive access to the name
# - Locking the network ensures exclusive access to the IP address allocation
def grab_address(session, fqdn, ip, network_environment=None,
                 dns_environment=None, comments=None,
                 allow_restricted_domain=False, allow_multi=False,
                 allow_reserved=False, relaxed=False, preclude=False):
    """
    Take ownership of an address.

    This is a bit complicated because due to DNS propagation delays, we want to
    allow users to pre-define a DNS address and then assign the address to a
    host later.

    Parameters:
        session: SQLA session handle
        fqdn: the name to allocate/take over
        ip: the IP address to allocate/take over
        network_environment: where the IP address lives
        dns_enviromnent: where the FQDN lives
        comments: any comments to attach to the DNS record if it is created as new
        allow_restricted_domain: if True, adding entries to restricted DNS
            domains is allowed, otherwise it is denied. Default is False.
        allow_multi: if True, allow the same FQDN to be added multiple times with
            different IP addresses. Deault is False.
        allow_reserved: if True, allow creating a ReservedName instead of an
            ARecord if no IP address was specified. Default is False.
        preclude: if True, forbid taking over an existing DNS record, even if it
            is not referenced by any AddressAssignment records. Default is
            False.
    """
    if not isinstance(network_environment, NetworkEnvironment):
        network_environment = NetworkEnvironment.get_unique_or_default(session,
                                                                       network_environment)
    if not dns_environment:
        dns_environment = network_environment.dns_environment
    elif not isinstance(dns_environment, DnsEnvironment):
        dns_environment = DnsEnvironment.get_unique(session, dns_environment,
                                                    compel=True)

    # Non-default DNS environments may contain anything, but we want to keep
    # the internal environment clean
    if dns_environment.is_default and not network_environment.is_default:
        raise ArgumentError("Entering external IP addresses to the "
                            "internal DNS environment is not allowed.")

    short, dbdns_domain = parse_fqdn(session, fqdn)

    # Lock the domain to prevent adding/deleting records while we're checking
    # FQDN etc. availability
    dbdns_domain.lock_row()

    if dbdns_domain.restricted and not allow_restricted_domain:
        raise ArgumentError("{0} is restricted, adding extra addresses "
                            "is not allowed.".format(dbdns_domain))

    dbfqdn = Fqdn.get_or_create(session, dns_environment=dns_environment,
                                name=short, dns_domain=dbdns_domain,
                                query_options=[joinedload('dns_records')])

    existing_record = None
    newly_created = False

    if ip:
        dbnetwork = get_net_id_from_ip(session, ip, network_environment)
        check_ip_restrictions(dbnetwork, ip, relaxed=relaxed)

        dbnetwork.lock_row()

        # No filtering on DNS environment. If an address is dynamic in one
        # environment, it should not be considered static in a different
        # environment.
        q = session.query(DynamicStub)
        q = q.filter_by(network=dbnetwork, ip=ip)
        dbdns_rec = q.first()
        _forbid_dyndns(dbdns_rec)

        # Verify that no other record uses the same IP address, this time taking
        # the DNS environemt into consideration.
        # While the DNS would allow different A records to point to the same IP
        # address, the current user expectation is that creating a DNS entry
        # also counts as a reservation, so we can not allow this use case. If we
        # want to implement such a feature later, the best way would be to
        # subclass Alias and let that subclass emit an A record instead of a
        # CNAME when the dump_dns command is called.
        q = session.query(ARecord)
        q = q.filter_by(network=dbnetwork, ip=ip)
        q = q.join(ARecord.fqdn)
        q = q.filter_by(dns_environment=dns_environment)
        dbrecords = q.all()
        if dbrecords and len(dbrecords) > 1:  # pragma: no cover
            # We're just trying to make sure this never happens
            raise AquilonError("IP address %s is referenced by multiple "
                               "DNS records: %s" %
                               (ip, ", ".join([format(rec, "a")
                                               for rec in dbrecords])))
        if dbrecords and dbrecords[0].fqdn != dbfqdn:
            raise ArgumentError("IP address {0} is already in use by {1:l}."
                                .format(ip, dbrecords[0]))

        # Check if the name is used already
        for dbdns_rec in dbfqdn.dns_records:
            if isinstance(dbdns_rec, ARecord):
                _forbid_dyndns(dbdns_rec)
                _check_netenv_compat(dbdns_rec, network_environment)
                if dbdns_rec.ip == ip and dbdns_rec.network == dbnetwork:
                    existing_record = dbdns_rec
                elif not allow_multi:
                    raise ArgumentError("{0} points to a different IP address."
                                        .format(dbdns_rec))

            elif isinstance(dbdns_rec, ReservedName):
                existing_record = convert_reserved_to_arecord(session,
                                                              dbdns_rec,
                                                              dbnetwork, ip)
                newly_created = True
            else:
                # Exclude aliases etc.
                raise ArgumentError("{0} cannot be used for address assignment."
                                    .format(dbdns_rec))

        if not existing_record:
            existing_record = ARecord(fqdn=dbfqdn, ip=ip, network=dbnetwork,
                                      comments=comments)
            session.add(existing_record)
            newly_created = True
    else:
        if not dbfqdn.dns_records:
            # There's no IP, and the name did not exist before. Create a
            # reservation, but only if the caller allowed that use case.
            if not allow_reserved:
                raise ArgumentError("DNS Record %s does not exist." % dbfqdn)

            existing_record = ReservedName(fqdn=dbfqdn, comments=comments)
            newly_created = True
        else:
            # There's no IP, but the name is already in use. We need a single IP
            # address.
            if len(dbfqdn.dns_records) > 1:
                raise ArgumentError("{0} does not resolve to a single IP address."
                                    .format(dbfqdn))

            existing_record = dbfqdn.dns_records[0]
            _forbid_dyndns(existing_record)
            if not isinstance(existing_record, ARecord):
                # Exclude aliases etc.
                raise ArgumentError("{0} cannot be used for address assignment."
                                    .format(existing_record))

            # Verify that the existing record is in the network environment the
            # caller expects
            _check_netenv_compat(existing_record, network_environment)

            ip = existing_record.ip
            dbnetwork = existing_record.network

            dbnetwork.lock_row()

    if existing_record.hardware_entity:
        raise ArgumentError("{0} is already used as the primary name of {1:cl} "
                            "{1.label}.".format(existing_record,
                                                existing_record.hardware_entity))

    if preclude and not newly_created:
        raise ArgumentError("{0} already exists.".format(existing_record))

    if ip:
        q = session.query(AddressAssignment)
        q = q.filter_by(ip=ip, network=dbnetwork)
        addr = q.first()
        if addr:
            raise ArgumentError("IP address {0} is already in use by "
                                "{1:l}.".format(ip, addr.interface))

    return (existing_record, newly_created)
