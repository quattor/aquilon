# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers to make getting and using hardware entities simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.hw.hardware_entity import HardwareEntity
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


