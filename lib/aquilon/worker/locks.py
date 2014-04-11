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

from aquilon.exceptions_ import InternalError
from aquilon.locks import LockQueue, LockKey
from aquilon.aqdb.model import Personality, ServiceInstance
from aquilon.worker.logger import CLIENT_INFO

LOGGER = logging.getLogger(__name__)


# Single instance of the LockQueue that should be used by any code
# in the broker.
lock_queue = LockQueue()


class NoLockKey(LockKey):
    """ A key that does not lock anything """
    def __init__(self, logger=LOGGER, loglevel=CLIENT_INFO):
        super(NoLockKey, self).__init__(logger=logger, loglevel=loglevel,
                                        lock_queue=lock_queue)
        self.transition("initialized")


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
        super(CompileKey, self).__init__(logger=logger, loglevel=loglevel,
                                         lock_queue=lock_queue)

        # Emulate the previous behavior:
        # - if no profile is provided, then this is a domain-wide lock
        # - if no domain is provided either, then this is a global lock
        if profile:
            if not domain:
                raise InternalError("Compile lock request for %s missing "
                                    "domain." % profile)
            self.shared["misc"].add("compile")
            self.shared["domain"].add(domain)
            self.exclusive["profile"].add(profile)
        elif domain:
            self.shared["misc"].add("compile")
            self.exclusive["domain"].add(domain)
        else:
            self.exclusive["misc"].add("compile")

        self.transition("initialized")


class PlenaryKey(LockKey):
    def __init__(self, personality=None, service_instance=None,
                 cluster_member=None, network_device=None, exclusive=True,
                 logger=LOGGER, loglevel=CLIENT_INFO):
        super(PlenaryKey, self).__init__(logger=logger, loglevel=loglevel,
                                         lock_queue=lock_queue)

        if exclusive:
            lockset = self.exclusive
        else:
            lockset = self.shared

        if personality:
            if isinstance(personality, Personality):
                key = "%s/%s" % (personality.archetype.name, personality.name)
            else:
                key = str(personality)
            lockset["personality"].add(key)
        if service_instance:
            if isinstance(service_instance, ServiceInstance):
                key = "%s/%s" % (service_instance.service.name,
                                 service_instance.name)
            else:
                key = str(service_instance)
            lockset["service"].add(key)
        if cluster_member:
            lockset["cluster_member"].add(str(cluster_member))
        if network_device:
            lockset["network_device"].add(str(network_device))

        # Make sure plenary updates conflict with the global compile lock, which
        # is used by e.g. the flush command.
        self.shared["misc"].add("compile")

        self.transition("initialized")


class SyncKey(LockKey):
    """
    Locks used by the refresh commands.

    This type of lock is intended to protect high-level commands from running in
    parallel.
    """
    def __init__(self, data, logger=LOGGER, loglevel=CLIENT_INFO):
        super(SyncKey, self).__init__(logger=logger, loglevel=loglevel,
                                      lock_queue=lock_queue)

        self.exclusive["sync"].add(data)
        self.transition("initialized")
