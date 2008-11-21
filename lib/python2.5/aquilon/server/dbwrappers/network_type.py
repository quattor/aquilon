# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a network type simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.network import NetworkType


def get_network_type(session, network_type_id):
    try:
        dbnetwork_type = session.query(NetworkType).filter_by(id=network_type_id).one()
    except InvalidRequestError, e:
        raise NotFoundException("NetworkType %s not found: %s" % (network_type, e))
    return network_type


