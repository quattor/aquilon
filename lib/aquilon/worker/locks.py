# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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


import logging

from aquilon.locks import LockQueue, LockKey
from aquilon.exceptions_ import InternalError
from aquilon.worker.logger import CLIENT_INFO

LOGGER = logging.getLogger(__name__)


# Single instance of the LockQueue that should be used by any code
# in the broker.
lock_queue = LockQueue()


# The concept of a "compile" lock somewhat oversimplifies.
# Broadly speaking there are four phases:
# 1 - Read plenary templates and profile templates for comparison.
# 2 - Write changed plenary templates and profile templates.
# 3 - Read relevant plenary, profile, cached profile, and domain
#     templates for compile.
# 4 - Copy (write) compiled profiles and cache profile templates.
#
# If in phase one it is determined that a template will not be
# changed and a certain lock is not needed, then that template
# must not be rewritten in phase two.
#
# The compile lock is described in terms of output profiles,
# which really only matter in phase four.  This seems like a
# relatively sane approach as generally the profile is the thing
# we actually care about being in a good state.
class CompileKey(LockKey):
    def __init__(self, domain=None, profile=None,
                 logger=LOGGER, loglevel=CLIENT_INFO):
        """Define the desired compile lock with a domain and a host.

        A profile could be a host or a cluster.

        """

        self.domain = domain
        self.profile = profile
        components = ["compile"]
        if self.domain:
            components.append(self.domain)
            if self.profile:
                components.append(self.profile)
        elif self.profile:
            raise InternalError("Compile lock request for %s missing domain." %
                                self.profile)
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel,
                         lock_queue=lock_queue)


class DeleteKey(LockKey):
    """Use when a broad deletion lock is required."""
    def __init__(self, group=None, logger=LOGGER, loglevel=CLIENT_INFO):
        self.group = group
        components = ["delete"]
        if self.group:
            components.append(self.group)
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel,
                         lock_queue=lock_queue)


class SyncKey(LockKey):
    """Locks used by the refresh commands."""
    def __init__(self, data=None, logger=LOGGER, loglevel=CLIENT_INFO):
        self.data = data
        components = ["sync"]
        if self.data:
            components.append(self.data)
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel,
                         lock_queue=lock_queue)
