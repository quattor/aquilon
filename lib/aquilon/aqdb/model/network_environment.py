# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2015,2019  Contributor
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

from sqlalchemy import Column, Integer, DateTime, Sequence, String, ForeignKey
from sqlalchemy.orm import deferred, relation

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import Base, Location, DnsEnvironment
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.config import Config

_TN = "network_environment"

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
    name = Column(AqStr(64), nullable=False, unique=True)

    location_id = Column(ForeignKey(Location.id), nullable=True, index=True)

    dns_environment_id = Column(ForeignKey(DnsEnvironment.id), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location)

    dns_environment = relation(DnsEnvironment, innerjoin=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)

    @property
    def is_default(self):
        return self.name == _config.get("site", "default_network_environment")

    @classmethod
    def get_default(cls, session):
        return cls.get_unique(
            session, _config.get("site", "default_network_environment"),
            compel=InternalError)

    @classmethod
    def get_unique_or_default(cls, session, network_environment=None):
        if network_environment:
            return cls.get_unique(session, network_environment, compel=True)
        else:
            return cls.get_default(session)


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


def get_net_dns_envs(session, all_network_environments=None,
                     network_environment=None,
                     exclude_network_environment=None,
                     mandatory_network_environment=True,
                     all_dns_environments=None,
                     dns_environment=None,
                     exclude_dns_environment=None,
                     mandatory_dns_environment=True, **_):
    """Prepare network and dns environments objects from parameters

    That function receives lists of network and dns environments to either
    include or exclude, as well as 'all' flags to consider all network/dns
    environments or not.
    Output are parsed lists or network and dns environments objects to filter
    with; if both the including and excluding lists are empty, it means that
    we should not filter by anything.
    """
    # As we want to manage both network environment inclusions and
    # exclusions, we first need to find all the specified environments
    # and put them in lists; these lists will then be used to filter
    # the results that match (inclusion) or don't match (exclusion) the
    # given environments
    dbnet_envs = []
    dbnet_envs_excl = []
    if not all_network_environments:
        if network_environment:
            dbnet_envs = [
                NetworkEnvironment.get_unique(session, netenv, compel=True)
                for netenv in network_environment
            ]
        if exclude_network_environment:
            dbnet_envs_excl = [
                NetworkEnvironment.get_unique(session, netenv, compel=True)
                for netenv in exclude_network_environment
            ]
        # In case no inclusion nor exclusion is specified, just use the
        # default network environment as inclusion
        if not dbnet_envs and not dbnet_envs_excl and \
                mandatory_network_environment:
            dbnet_envs = [NetworkEnvironment.get_default(session)]

    # As we did above for the network environments, we do for the dns
    # environments, as both of thos eare heavily linked, so allowing
    # inclusion/exclusion on the network environment side requires us to
    # manage it properly (and the same way) on the dns environment side
    dbdns_envs = []
    dbdns_envs_excl = []
    if not all_dns_environments:
        if dns_environment:
            dbdns_envs = [
                DnsEnvironment.get_unique(session, dnsenv, compel=True)
                for dnsenv in dns_environment
            ]
        if exclude_dns_environment:
            dbdns_envs_excl = [
                DnsEnvironment.get_unique(session, dnsenv, compel=True)
                for dnsenv in exclude_dns_environment
            ]
        # In case no inclusion nor exclusion is specified, compute the
        # inclusion/exclusion as the dns environments related to the
        # included/excluded network environments
        if not dbdns_envs and not dbdns_envs_excl and \
                not all_network_environments:
            if dbnet_envs or dbnet_envs_excl:
                dbdns_envs = [dbnetenv.dns_environment
                              for dbnetenv in dbnet_envs]
                dbdns_envs_excl = [dbnetenv.dns_environment
                                   for dbnetenv in dbnet_envs_excl]
            elif mandatory_dns_environment:
                dbdns_envs = [DnsEnvironment.get_default(session)]

    return (dbnet_envs, dbnet_envs_excl, dbdns_envs, dbdns_envs_excl)
