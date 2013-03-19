# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
""" DNS SRV records """

import re

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref, object_session, validates
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import AquilonError, ArgumentError
from aquilon.aqdb.model import DnsRecord, Fqdn, ARecord, Alias

_TN = 'srv_record'
_name_re = re.compile(r'_([^_.]+)\._([^_.]+)$')

PROTOCOLS = ['tcp', 'udp']


class SrvRecord(DnsRecord):
    __tablename__ = _TN
    _class_label = "SRV Record"

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                               name='%s_dns_record_fk' % _TN,
                                               ondelete='CASCADE'),
                           primary_key=True)

    priority = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    port = Column(Integer, nullable=False)

    target_id = Column(Integer, ForeignKey('fqdn.id',
                                           name='%s_target_fk' % _TN),
                       nullable=False)

    target = relation(Fqdn, primaryjoin=target_id == Fqdn.id,
                      backref=backref('srv_records'))

    target_rrs = association_proxy('target', 'dns_records')

    __mapper_args__ = {'polymorphic_identity': _TN}

    @validates('priority', 'weight', 'port')
    def validate_ushort(self, key, value):
        value = int(value)
        if key == 'port':
            min = 1
        else:
            min = 0
        if value < min or value > 65535:
            raise ArgumentError("The %s must be between %d and 65535." %
                                (key, min))
        return value

    @property
    def service(self):
        m = _name_re.match(self.fqdn.name)
        if not m:  # pragma: no cover
            raise AquilonError("Malformed SRV FQDN in AQDB: %s" % self.fqdn)
        return m.group(1)

    @property
    def protocol(self):
        m = _name_re.match(self.fqdn.name)
        if not m:  # pragma: no cover
            raise AquilonError("Malformed SRV FQDN in AQDB: %s" % self.fqdn)
        return m.group(2)

    def __init__(self, service, protocol, dns_domain, dns_environment, priority,
                 weight, port, target, **kwargs):
        if not isinstance(target, Fqdn):  # pragma: no cover
            raise TypeError("The target of an SRV record must be an Fqdn.")
        session = object_session(target)
        if not session:  # pragma: no cover
            raise AquilonError("The target name must already be part of "
                               "the session.")
        # SRV records are special, as the FQDN is managed internally
        if "fqdn" in kwargs:  # pragma: no cover
            raise AquilonError("SRV records do not accept an FQDN argument.")

        self.validate_ushort('priority', priority)
        self.validate_ushort('weight', weight)
        self.validate_ushort('port', port)

        # RFC 2782:
        # - there must be one or more address records for the target
        # - the target must not be an alias
        found_address = False
        for rr in target.dns_records:
            if isinstance(rr, ARecord):
                found_address = True
            elif isinstance(rr, Alias):
                raise ArgumentError("The target of an SRV record must not be "
                                    "an alias.")
        if not found_address:
            raise ArgumentError("The target of an SRV record must resolve to "
                                "one or more addresses.")

        if protocol not in PROTOCOLS:
            raise ArgumentError("Unknown protocol %s." % protocol)
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())

        # Disable autoflush because self is not ready to be pushed to the DB yet
        with session.no_autoflush:
            fqdn = Fqdn.get_or_create(session, name=name, dns_domain=dns_domain,
                                      dns_environment=dns_environment,
                                      ignore_name_check=True)

            # Do not allow two SRV records pointing at the same target
            for rr in fqdn.dns_records:
                if isinstance(rr, SrvRecord) and rr.target == target and \
                   rr.protocol == protocol and rr.service == service:
                    raise ArgumentError("{0} already exists.".format(rr))

        super(SrvRecord, self).__init__(fqdn=fqdn, priority=priority, weight=weight,
                                        port=port, target=target, **kwargs)


srv_record = SrvRecord.__table__  # pylint: disable=C0103
srv_record.primary_key.name = '%s_pk' % _TN
srv_record.info["unique_fields"] = ["fqdn"]
srv_record.info["extra_search_fields"] = ['target', 'dns_environment']
