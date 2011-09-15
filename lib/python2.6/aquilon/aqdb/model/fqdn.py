# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
""" Representation of Fully Qualified Domain Names """

from datetime import datetime

from sqlalchemy import (Integer, DateTime, Sequence, Column, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.orm.session import Session

from aquilon.exceptions_ import InternalError, ArgumentError
from aquilon.aqdb.model import Base, DnsDomain, DnsEnvironment
from aquilon.aqdb.model.base import _raise_custom
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr


_TN = "fqdn"


class Fqdn(Base):
    __tablename__ = _TN
    _instance_label = 'fqdn'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(63), nullable=False)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='%s_dns_domain_fk' % _TN),
                           nullable=False)

    dns_environment_id = Column(Integer, ForeignKey('dns_environment.id',
                                                    name='%s_dns_env_fk' % _TN),
                                nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    dns_domain = relation(DnsDomain, innerjoin=True, backref=backref("fqdns"))

    dns_environment = relation(DnsEnvironment, innerjoin=True,
                               backref=backref("fqdns"))

    @property
    def fqdn(self):
        return self.name + '.' + self.dns_domain.name

    @classmethod
    def get_unique(cls, session, fqdn=None, dns_environment=None, name=None,
                   dns_domain=None, **kwargs):
        if fqdn:
            if name or dns_domain:  # pragma: no cover
                raise TypeError("fqdn and name/dns_domain should not be mixed")
            (name, dns_domain) = parse_fqdn(session, fqdn)

        if not isinstance(dns_environment, DnsEnvironment):
            dns_environment = DnsEnvironment.get_unique_or_default(session,
                                                                   dns_environment)
        return super(Fqdn, cls).get_unique(session, name=name,
                                           dns_domain=dns_domain,
                                           dns_environment=dns_environment,
                                           **kwargs)

    @classmethod
    def get_or_create(cls, session, dns_environment=None, preclude=False,
                      **kwargs):
        fqdn = cls.get_unique(session, dns_environment=dns_environment, **kwargs)
        if fqdn:
            if preclude:
                _raise_custom(preclude, ArgumentError, "{0} already exists.")
            return fqdn

        if not isinstance(dns_environment, DnsEnvironment):
            dns_environment = DnsEnvironment.get_unique_or_default(session,
                                                                   dns_environment)

        fqdn = cls(session=session, dns_environment=dns_environment, **kwargs)
        session.add(fqdn)
        session.flush()
        return fqdn

    @classmethod
    def check_name(cls, name, dns_domain):
        """ Validate the name parameter """

        if not isinstance(name, basestring):  # pragma: no cover
            raise TypeError("%s: name must be a string." % cls.name)
        if not isinstance(dns_domain, DnsDomain):  # pragma: no cover
            raise TypeError("%s: dns_domain must be a DnsDomain." % cls.name)

        DnsDomain.check_label(name)

        # The limit for DNS name length is 255, assuming wire format. This
        # translates to 253 for simple ASCII text; see:
        # http://www.ops.ietf.org/lists/namedroppers/namedroppers.2003/msg00964.html
        if len(name) + 1 + len(dns_domain.name) > 253:
            raise ArgumentError('The fully qualified domain name is too long.')

    def _check_session(self, session):
        if not session or not isinstance(session, Session):  # pragma: no cover
            raise InternalError("%s needs a session." % self._get_class_label())

    def __init__(self, session=None, name=None, dns_domain=None, fqdn=None,
                 dns_environment=None, **kwargs):
        if fqdn:
            if name or dns_domain:  # pragma: no cover
                raise TypeError("fqdn and name/dns_domain should not be mixed")
            self._check_session(session)
            (name, dns_domain) = parse_fqdn(session, fqdn)

        self.check_name(name, dns_domain)

        if not isinstance(dns_environment, DnsEnvironment):
            self._check_session(session)
            dns_environment = DnsEnvironment.get_unique_or_default(session,
                                                                   dns_environment)

        super(Fqdn, self).__init__(name=name, dns_domain=dns_domain,
                                   dns_environment=dns_environment, **kwargs)


fqdn = Fqdn.__table__  # pylint: disable-msg=C0103, E1101
fqdn.primary_key.name = '%s_pk' % _TN
fqdn.append_constraint(UniqueConstraint('name', 'dns_domain_id',
                                        'dns_environment_id',
                                        name='%s_name_domain_env_uk' % _TN))

fqdn.info['unique_fields'] = ['dns_environment', 'dns_domain', 'name']
