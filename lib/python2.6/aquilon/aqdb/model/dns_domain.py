# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" DNS Domains, as simple names """

from datetime import datetime
import re

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        UniqueConstraint)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import deferred

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'dns_domain'


def parse_fqdn(session, fqdn):
    """ Break an fqdn (string) and get some useful information from it.

        Returns a tuple of the shortname (string), and DnsDomain object
    """
    if not fqdn:
        raise ArgumentError("No fully qualified name specified.")

    (short, dot, dns_domain) = fqdn.partition(".")

    if not dns_domain:
        raise ArgumentError("FQDN '%s' is not valid, it does not contain a "
                            "domain." % fqdn)
    if not short:
        raise ArgumentError("FQDN '%s' is not valid, missing host "
                            "name." % fqdn)
    dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
    return (short, dbdns_domain)


class DnsDomain(Base):
    """ Dns Domain (simple names that compose bigger records) """

    __tablename__ = _TN
    _class_label = 'DNS Domain'

    # RFC 1035
    _name_check = re.compile('^[a-zA-Z]([-a-zA-Z0-9]*[a-zA-Z0-9])?$')

    id = Column(Integer, Sequence('%s_id_seq' % (_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    restricted = Column(Boolean(name="%s_restricted_ck" % _TN),
                        nullable=False, default=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    servers = association_proxy('_ns_records', 'a_record')

    # The relation is defined in dns_map.py
    mapped_locations = association_proxy('dns_maps', 'location')

    @classmethod
    def check_label(cls, label):  # TODO: database check constraint for length
        if len(label) < 1 or len(label) > 63:
            msg = 'DNS name components must have a length between 1 and 63.'
            raise ArgumentError(msg)
        if not cls._name_check.match(label):
            raise ArgumentError("Illegal DNS name format '%s'." % label)

    def __init__(self, *args, **kwargs):

        if 'name' not in kwargs:
            raise KeyError('DNS domain name missing.')

        domain = kwargs['name']

        # The limit for DNS name length is 255, assuming wire format. This
        # translates to 253 for simple ASCII text; see:
        # http://www.ops.ietf.org/lists/namedroppers/namedroppers.2003/msg00964.html
        if len(domain) > 253:
            raise ArgumentError('The DNS domain name is too long.')

        parts = domain.split('.')
        if len(parts) < 2:
            raise ArgumentError('Top-level DNS domains cannot be added.')
        # The limit of max. 127 parts mentioned at various documents about DNS
        # follows from the other checks above and below
        for part in parts:
            self.check_label(part)

        super(DnsDomain, self).__init__(*args, **kwargs)


dnsdomain = DnsDomain.__table__  # pylint: disable=C0103

dnsdomain.primary_key.name = '%s_pk' % (_TN)
dnsdomain.append_constraint(UniqueConstraint('name', name='%s_uk' % (_TN)))
dnsdomain.info['unique_fields'] = ['name']
