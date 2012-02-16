# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
""" NS Records tell us what name servers to use for a given Dns Domain """
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, DnsDomain, ARecord

_TN = 'ns_record'


class NsRecord(Base):
    """ NS Records tell us what name servers to use for a given Dns Domain """
    __tablename__ = _TN
    _class_label = "Name Server"

    a_record_id = Column(Integer, ForeignKey(ARecord.dns_record_id,
                                             name='%s_a_record_fk' % (_TN)),
                         primary_key=True)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='%s_domain_fk' % (_TN)),
                           primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    a_record = relation(ARecord, lazy=False, innerjoin=True,
                        backref=backref('_ns_records', cascade='all'))

    dns_domain = relation(DnsDomain, lazy=False, innerjoin=True,
                          backref=backref('_ns_records', cascade='all'))

    def __format__(self, format_spec):
        instance = "%s [%s] of DNS Domain %s" % (self.a_record.fqdn,
                                                 self.a_record.ip,
                                                 self.dns_domain.name)
        return self.format_helper(format_spec, instance)

    def __repr__(self):
        msg = '<%s dns_domain=%s %s>' % (self.__class__.__name__,
                                         self.dns_domain.name,
                                         self.a_record.fqdn)
        return msg

    def _get_instance_label(self):
        return "{0:a} of {1:l}".format(self.a_record, self.dns_domain)


nsrecord = NsRecord.__table__  # pylint: disable=C0103, E1101
nsrecord.info['unique_fields'] = ['a_record', 'dns_domain']
nsrecord.primary_key.name = '%s_pk' % _TN

# Association proxies from/to NSRecord:
# DnsDomain.servers = association_proxy('_name_servers', 'a_record')

#TODO: proxy all IP addresses through to DnsDomains when System is removed
