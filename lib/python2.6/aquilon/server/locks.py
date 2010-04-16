# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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


import logging
from threading import Condition, Lock

from aquilon.locks import LockQueue, LockKey
from aquilon.exceptions_ import InternalError
from aquilon.server.logger import CLIENT_INFO

LOGGER = logging.getLogger('aquilon.server.locks')


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
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel)


class DeleteKey(LockKey):
    """Use when a broad deletion lock is required."""
    def __init__(self, group=None, logger=LOGGER, loglevel=CLIENT_INFO):
        self.group = group
        components = ["delete"]
        if self.group:
            components.append(self.group)
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel)


class SyncKey(LockKey):
    """Locks used by the refresh commands."""
    def __init__(self, data=None, logger=LOGGER, loglevel=CLIENT_INFO):
        self.data = data
        components = ["sync"]
        if self.data:
            components.append(self.data)
        LockKey.__init__(self, components, logger=logger, loglevel=loglevel)
