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
    comments = Column(String(255), nullable=True)

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
