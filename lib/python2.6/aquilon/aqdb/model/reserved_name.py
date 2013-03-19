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
""" DnsRecords are higher level constructs which can provide services """

from sqlalchemy import Integer, Column, ForeignKey

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import DnsRecord


class ReservedName(DnsRecord):
    """
        ReservedName is a placeholder for a name that does not have an IP
        address.
    """

    __tablename__ = 'reserved_name'
    __mapper_args__ = {'polymorphic_identity': 'reserved_name'}
    _class_label = 'Reserved Name'

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                           name='reserved_name_dns_record_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    def __init__(self, **kwargs):
        if "ip" in kwargs and kwargs["ip"]:  # pragma: no cover
            raise ArgumentError("Reserved names must not have an IP address.")
        super(ReservedName, self).__init__(**kwargs)


resname = ReservedName.__table__  # pylint: disable=C0103
resname.primary_key.name = 'reserved_name_pk'
resname.info['unique_fields'] = ['fqdn']
resname.info['extra_search_fields'] = ['dns_environment']
