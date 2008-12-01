""" Enum column type for network table """
from exceptions import TypeError

import sqlalchemy


_NETWORK_TYPES = ['transit', 'vip', 'management', 'unknown', 'grid_domain',
                  'legacy', 'stretch']

class NetworkTypeError(TypeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Illegal NetworkType '%s'" % self.value

class NetworkType(sqlalchemy.types.TypeDecorator):
    """a type that decorates String, and serves as an enum-like value check
       for the network table"""

    impl = sqlalchemy.types.String

    def process_bind_param(self, value, engine):
        value = value.strip().lower()
        if value in _NETWORK_TYPES:
            return value
        else:
            raise NetworkTypeError(value)

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return NetworkType(self.impl.length)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
