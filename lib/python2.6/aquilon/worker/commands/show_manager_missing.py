# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq show manager --missing`."""

from sqlalchemy.orm import contains_eager

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.interface import MissingManagersList
from aquilon.aqdb.model import (Interface, AddressAssignment, HardwareEntity,
                                DnsRecord, DnsDomain, Fqdn)


class CommandShowManagerMissing(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Interface)
        q = q.filter_by(interface_type='management')
        q = q.outerjoin(AddressAssignment)
        q = q.filter(AddressAssignment.id == None)
        q = q.reset_joinpoint()

        q = q.join(HardwareEntity)
        q = q.filter_by(hardware_type='machine')
        q = q.options(contains_eager('hardware_entity'))

        # MissingManagerList wants the fqdn, so get it in one go
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('hardware_entity.primary_name'))
        q = q.options(contains_eager('hardware_entity.primary_name.fqdn'))
        q = q.options(contains_eager('hardware_entity.primary_name.fqdn.dns_domain'))

        # Order by FQDN if it exists, otherwise fall back to the label
        q = q.order_by(Fqdn.name, DnsDomain.name, HardwareEntity.label)
        return MissingManagersList(q.all())
