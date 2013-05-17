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
""" Environments in DNS are groups of network segments. """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        UniqueConstraint)
from sqlalchemy.orm import deferred

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.config import Config

_TN = 'dns_environment'

_config = Config()


class DnsEnvironment(Base):
    """
        Dns Environments are groups of network segments that have their own
        distinct view of DNS data. This could be the internal institutional
        network, the external, the dmz, or other corporate segments.

        For now, SRV Records and aliases may not cross environment boundaries

    """
    __tablename__ = _TN
    _class_label = 'DNS Environment'

    id = Column(Integer, Sequence('%s_id_seq' % (_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    @property
    def is_default(self):
        return self.name == _config.get("site", "default_dns_environment")

    @classmethod
    def get_unique_or_default(cls, session, dns_environment=None):
        if dns_environment:
            return cls.get_unique(session, dns_environment, compel=True)
        else:
            return cls.get_unique(session, _config.get("site",
                                                       "default_dns_environment"),
                                  compel=InternalError)


dnsenv = DnsEnvironment.__table__  # pylint: disable=C0103

dnsenv.primary_key.name = '%s_pk' % _TN
dnsenv.append_constraint(UniqueConstraint('name', name='%s_name_uk' % _TN))
dnsenv.info['unique_fields'] = ['name']
