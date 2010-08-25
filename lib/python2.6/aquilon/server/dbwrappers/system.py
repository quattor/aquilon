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
"""Wrappers to make getting and using systems simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.model import DnsDomain, System
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.server.dbwrappers.network import get_network_byip


def get_system(session, system, system_type=System, system_label='FQDN'):
    (short, dbdns_domain) = parse_fqdn(session, system)
    return get_system_from_parts(session, short, dbdns_domain, system_type,
                                 system_label)

def get_system_from_parts(session, short, dbdns_domain, system_type=System,
                          system_label='FQDN'):
    try:
        q = session.query(system_type)
        q = q.filter_by(name=short, dns_domain=dbdns_domain)
        dbsystem = q.first()
        if not dbsystem:
            raise NotFoundException("%s %s.%s not found." %
                                    (system_label, short, dbdns_domain.name))
    except InvalidRequestError, e:
        raise AquilonError("Failed to find %s %s.%s: %s" %
                                (system_label, short, dbdns_domain.name, e))
    return dbsystem

def parse_system_and_verify_free(session, system):
    (short, dbdns_domain) = parse_fqdn(session, system)
    q = session.query(System)
    dbsystem = q.filter_by(name=short, dns_domain=dbdns_domain).first()
    if dbsystem:
        raise ArgumentError("{0} already exists.".format(dbsystem))
    return (short, dbdns_domain)

def search_system_query(session, system_type=System, **kwargs):
    q = session.query(system_type)
    # Outer-join in all the subclasses so that each access of
    # system doesn't (necessarily) issue another query.
    if system_type is System:
        q = q.with_polymorphic(System.__mapper__.polymorphic_map.values())
    if kwargs.get('fqdn', None):
        (short, dbdns_domain) = parse_fqdn(session, kwargs['fqdn'])
        q = q.filter_by(name=short, dns_domain=dbdns_domain)
    if kwargs.get('dns_domain', None):
        dbdns_domain = DnsDomain.get_unique(session, kwargs['dns_domain'],
                                            compel=True)
        q = q.filter_by(dns_domain=dbdns_domain)
    if kwargs.get('shortname', None):
        q = q.filter_by(name=kwargs['shortname'])
    if kwargs.get('ip', None):
        q = q.filter_by(ip=kwargs['ip'])
    if kwargs.get('networkip', None):
        dbnetwork = get_network_byip(session, kwargs['networkip'])
        q = q.filter_by(network=dbnetwork)
    if kwargs.get('mac', None):
        q = q.filter_by(mac=kwargs['mac'])
    if kwargs.get('type', None):
        # Deprecated... remove if it becomes a problem.
        type_arg = kwargs['type'].strip().lower()
        if type_arg == 'tor_switch':
            type_arg = 'switch'
        q = q.filter_by(system_type=type_arg)
    return q

def get_system_dependencies(session, dbsystem):
    """Return a list of strings describing how a system is being used.

    An empty list will be returned if there are no dependencies.

    """
    ret = []
    for sis in dbsystem.sislist:
        ret.append("%s is bound as a server for service %s instance %s" %
                   (sis.system.fqdn, sis.service_instance.service.name,
                    sis.service_instance.name))
    return ret
