# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
""" Helper functions for change management """

import re

from aquilon.exceptions_ import AuthorizationException, ArgumentError
from aquilon.worker.dbwrappers.personality import is_prod_personality_used

TCM_RE = re.compile(r"^tcm=([0-9]+)$", re.IGNORECASE)
SN_RE = re.compile(r"^sn=([a-z]+[0-9]+)$", re.IGNORECASE)
EMERG_RE = re.compile("emergency")


def validate_justification(principal, justification, reason):
    result = None
    for valid_re in [TCM_RE, SN_RE, EMERG_RE]:
        result = valid_re.search(justification)
        if result:
            break
    if not result:
        raise ArgumentError("Failed to parse the justification: expected "
                            "tcm=NNNNNNNNN or sn=XXXNNNNN.")
    if justification == 'emergency' and not reason:
        raise AuthorizationException("Justification of 'emergency' requires "
                                     "--reason to be specified.")

    # TODO: EDM validation
    # edm_validate(result.group(0))


def validate_personality_justification(dbpersona, user, justification, reason):
    if is_prod_personality_used(dbpersona):
        if not justification:
            raise AuthorizationException(
                "{0} is marked production and is under "
                "change management control. Please specify "
                "--justification or --justification='emergency' and reason.".format(dbpersona))

        validate_justification(user, justification, reason)
