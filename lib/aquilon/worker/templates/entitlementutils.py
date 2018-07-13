# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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

from collections import defaultdict

from aquilon.aqdb.model import (
    EntitlementOnHostEnvironment,
    EntitlementOnLocation,
)
from aquilon.worker.templates.panutils import (
    pan_append,
)


def flatten_entitlements(lines, dbobj, prefix=''):
    """Flatten entitlements for plenaries

    This allows to flatten the entitlements of a given dbobj to be stored
    in the plenaries; this will store all the details of the entitlements
    for the given entitlements type.
    A prefix can be specified to prepend the path of system/entitlements.
    """
    entitlements = defaultdict(lambda: defaultdict(set))

    dbloc = getattr(dbobj, 'location', None)
    dbenv = getattr(dbobj, 'host_environment', None)

    def add(to_type, value, entit, **extra):
        data = [('value', value)] + extra.items()

        # If it is for a specific location that does not match
        if isinstance(entit, EntitlementOnLocation) and \
                dbloc != entit.location:
            return

        # If it is for a specific environment that does not match
        if isinstance(entit, EntitlementOnHostEnvironment) and \
                dbenv != entit.host_environment:
            return

        entitlements[entit.type.name][to_type].add(tuple(data))

    for entit in dbobj.entitled_users:
        value = entit.user.name
        add('user', value, entit, type=entit.user.type.name)

    for entit in dbobj.entitled_grns:
        value = entit.eon_id
        add('eon_id', value, entit)

    for entit_type, entit_values in entitlements.items():
        for k, v in entit_values.items():
            path = '{}system/entitlements/{}/{}'.format(prefix, entit_type, k)
            for entry in sorted(dict(vv) for vv in v):
                pan_append(lines, path, entry)
