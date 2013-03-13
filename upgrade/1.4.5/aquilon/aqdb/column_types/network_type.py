# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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


