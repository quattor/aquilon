# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq show manager --missing`."""

from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import exists

from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.interface import MissingManagersList
from aquilon.aqdb.model import (Interface, AddressAssignment, HardwareEntity,
                                PrimaryNameAssociation, DnsRecord, DnsDomain)


class CommandShowManagerMissing(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Interface)
        q = q.filter_by(interface_type='management')
        q = q.filter(~exists().where(AddressAssignment.interface_id ==
                                     Interface.id))
        q = q.reset_joinpoint()
        q = q.join(HardwareEntity)
        q = q.filter_by(hardware_type='machine')
        q = q.options(contains_eager('hardware_entity'))

        # MissingManagerList wants the fqdn, so get it in one go
        q = q.outerjoin(PrimaryNameAssociation, DnsRecord, DnsDomain)
        q = q.options(contains_eager('hardware_entity._primary_name_asc'))
        q = q.options(contains_eager('hardware_entity._primary_name_asc.'
                                     'dns_record'))
        q = q.options(contains_eager('hardware_entity._primary_name_asc.'
                                     'dns_record.dns_domain'))

        # Order by FQDN if it exists, otherwise fall back to the label
        q = q.order_by(DnsRecord.name, DnsDomain.name, HardwareEntity.label)
        return MissingManagersList(q.all())
