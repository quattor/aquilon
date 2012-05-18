# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Resource, AddressAssignment, ARecord

_TN = 'service_address'
_ABV = 'srv_addr'


class ServiceAddress(Resource):
    """ Service address resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}
    _class_label = 'Service Address'

    resource_id = Column(Integer, ForeignKey('resource.id',
                                             name='%s_resource_fk' % _ABV),
                         primary_key=True)

    # This is not normalized, as we could get the same object by
    # self.assignments[0].dns_records[0], but this way it's faster
    dns_record_id = Column(Integer, ForeignKey('a_record.dns_record_id',
                                               name='%s_arecord_fk' % _ABV),
                           nullable=False)

    assignments = relation(AddressAssignment, cascade="all, delete-orphan",
                           passive_deletes=True,
                           backref=backref('service_address'))

    dns_record = relation(ARecord, innerjoin=True,
                          backref=backref('service_address', uselist=False))

    @property
    def interfaces(self):
        ifaces = []
        for addr in self.assignments:
            if addr.interface.name not in ifaces:
                ifaces.append(addr.interface.name)

        ifaces.sort()
        return ifaces


srvaddr = ServiceAddress.__table__
srvaddr.primary_key.name = '%s_pk' % (_TN)
srvaddr.info['unique_fields'] = ['name', 'holder']
