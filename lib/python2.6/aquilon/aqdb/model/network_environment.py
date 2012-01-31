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
""" Network environments """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import deferred, relation

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import Base, Location, DnsEnvironment
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.config import Config

_TN = "network_environment"
_ABV = "net_env"

_config = Config()


class NetworkEnvironment(Base):
    """
    Network Environment

    Represents an administrative domain for RFC 1918 private network addresses.
    Network addresses are unique inside an environment, but different
    environments may have duplicate/overlapping network definitions. It is
    expected that when two hosts have IP addresses in two different network
    environments, then they can not communicate directly with each other.
    """

    __tablename__ = _TN
    _class_label = 'Network Environment'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(AqStr(64), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                             name='%s_loc_fk' % _ABV),
                         nullable=True)

    dns_environment_id = Column(Integer, ForeignKey('dns_environment.id',
                                                    name='%s_dns_env_fk' % _ABV),
                                nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location)

    dns_environment = relation(DnsEnvironment)

    @property
    def is_default(self):
        return self.name == _config.get("site", "default_network_environment")

    @classmethod
    def get_unique_or_default(cls, session, network_environment=None):
        if network_environment:
            return cls.get_unique(session, network_environment, compel=True)
        else:
            return cls.get_unique(session, _config.get("site",
                                                       "default_network_environment"),
                                  compel=InternalError)


netenv = NetworkEnvironment.__table__  # pylint: disable=C0103, E1101
netenv.primary_key.name = '%s_pk' % _TN

netenv.append_constraint(UniqueConstraint('name', name='%s_name_uk' % _ABV))
netenv.info['unique_fields'] = ['name']
