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
""" DnsRecords are higher level constructs which can provide services """

from sqlalchemy import Integer, Column, ForeignKey

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import DnsRecord

_TN = "reserved_name"


class ReservedName(DnsRecord):
    """
        ReservedName is a placeholder for a name that does not have an IP
        address.
    """

    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}
    _class_label = 'Reserved Name'

    dns_record_id = Column(Integer, ForeignKey(DnsRecord.id,
                                               name='%s_dns_record_fk' % _TN,
                                               ondelete='CASCADE'),
                           primary_key=True)

    def __init__(self, **kwargs):
        if "ip" in kwargs and kwargs["ip"]:  # pragma: no cover
            raise ArgumentError("Reserved names must not have an IP address.")
        super(ReservedName, self).__init__(**kwargs)


resname = ReservedName.__table__  # pylint: disable=C0103
resname.info['unique_fields'] = ['fqdn']
resname.info['extra_search_fields'] = ['dns_environment']
