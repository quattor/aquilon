# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

    location_id = Column(Integer, ForeignKey(Location.id,
                                             name='%s_loc_fk' % _ABV),
                         nullable=True)

    dns_environment_id = Column(Integer, ForeignKey(DnsEnvironment.id,
                                                    name='%s_dns_env_fk' % _ABV),
                                nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location)

    dns_environment = relation(DnsEnvironment, innerjoin=True)

    __table_args__ = (UniqueConstraint(name, name='%s_name_uk' % _ABV),)

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

netenv = NetworkEnvironment.__table__  # pylint: disable=C0103
netenv.info['unique_fields'] = ['name']


def get_net_dns_env(session, network_environment=None,
                    dns_environment=None):
    dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                         network_environment)
    if dns_environment:
        dbdns_env = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)
    else:
        dbdns_env = dbnet_env.dns_environment

    return (dbnet_env, dbdns_env)
