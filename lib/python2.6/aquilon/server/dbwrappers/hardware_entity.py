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
"""Wrappers to make getting and using hardware entities simpler."""


from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.model import HardwareEntity, Vendor
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model


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
        if kwargs.get('machine_type') and \
           dbmodel.machine_type != kwargs['machine_type']:
            raise ArgumentError("machine_type %s conflicts with model %s "
                                "where machine_type is %s" %
                                (kwargs['machine_type'], dbmodel.name,
                                 dbmodel.machine_type))
        if kwargs.get('vendor') and \
           dbmodel.vendor.name != kwargs['vendor']:
            raise ArgumentError("vendor %s conflicts with model %s "
                                "where vendor is %s" %
                                (kwargs['vendor'], dbmodel.name,
                                 dbmodel.vendor.name))
    if kwargs.get('vendor') or kwargs.get('machine_type'):
        q = q.join(['model'])
        if kwargs.get('vendor'):
            dbvendor = Vendor.get_unique(session, kwargs['vendor'], compel=True)
            q = q.filter_by(vendor=dbvendor)
        if kwargs.get('machine_type'):
            q = q.filter_by(machine_type=kwargs['machine_type'])
        q = q.reset_joinpoint()
    if kwargs.get('mac') or kwargs.get('pg'):
        q = q.join('interfaces')
        if kwargs.get('mac'):
            q = q.filter_by(mac=kwargs['mac'])
        if kwargs.get('pg'):
            q = q.filter_by(port_group=kwargs['pg'])
        q = q.reset_joinpoint()
    if kwargs.get('serial', None):
        q = q.filter_by(serial_no=kwargs['serial'])
    return q