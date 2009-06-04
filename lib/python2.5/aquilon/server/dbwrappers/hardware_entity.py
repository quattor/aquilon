# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Wrappers to make getting and using hardware entities simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.model import HardwareEntity
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.vendor import get_vendor


def search_hardware_entity_query(session, hardware_entity_type=HardwareEntity,
                                 **kwargs):
    q = session.query(hardware_entity_type)
    if hardware_entity_type is HardwareEntity:
        q = q.with_polymorphic(
            HardwareEntity.__mapper__.polymorphic_map.values())
    dblocation = get_location(session, **kwargs)
    if dblocation:
        q = q.filter_by(location=dblocation)
    if kwargs.get('model', None):
        dbmodel = get_model(session, kwargs['model'])
        q = q.filter_by(model=dbmodel)
    if kwargs.get('vendor', None):
        dbvendor = get_vendor(session, kwargs['vendor'])
        q = q.join(['model'])
        q = q.filter_by(vendor=dbvendor)
        q = q.reset_joinpoint()
    if kwargs.get('mac', None):
        q = q.join('interfaces')
        q = q.filter_by(mac=kwargs['mac'])
        q = q.reset_joinpoint()
    if kwargs.get('serial', None):
        q = q.filter_by(serial_no=kwargs['serial'])
    return q
