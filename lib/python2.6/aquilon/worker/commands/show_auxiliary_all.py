# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq show auxiliary --all`."""

from sqlalchemy.orm import contains_eager, aliased
from sqlalchemy.sql import exists

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (Interface, AddressAssignment, HardwareEntity,
                                ARecord, DnsDomain, Fqdn)


class CommandShowAuxiliaryAll(BrokerCommand):

    def render(self, session, **arguments):
        # An auxiliary...
        q = session.query(ARecord)
        # ... is not a primary name...
        q = q.outerjoin(HardwareEntity)
        q = q.filter(HardwareEntity.id == None)
        q = q.reset_joinpoint()
        # ... and is assigned to a public interface...
        q = q.join((AddressAssignment, ARecord.ip == AddressAssignment.ip))
        q = q.join(Interface)
        q = q.filter_by(interface_type='public')
        # ... of a machine.
        q = q.join(aliased(HardwareEntity))
        q = q.filter_by(hardware_type='machine')
        q = q.reset_joinpoint()
        q = q.join(Fqdn, DnsDomain)
        q = q.options(contains_eager('fqdn'))
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(Fqdn.name, DnsDomain.name)
        fqdns = [rec.fqdn for rec in q.all()]
        return fqdns
