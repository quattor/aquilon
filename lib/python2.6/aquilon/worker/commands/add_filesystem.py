# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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


from aquilon.aqdb.model import Filesystem
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddFilesystem(BrokerCommand):

    required_parameters = ["filesystem", "mountpoint", "blockdevice",
                           "type", "bootmount"]

    def render(self, session, logger, filesystem, type, mountpoint,
               blockdevice, bootmount,
               dumpfreq, fsckpass, options,
               hostname, cluster, resourcegroup,
               comments, **arguments):

        validate_basic("filesystem", filesystem)
        holder = get_resource_holder(session, hostname, cluster, resourcegroup,
                                     compel=False)

        Filesystem.get_unique(session, name=filesystem, holder=holder,
                              preclude=True)

        if dumpfreq is None:
            dumpfreq = 0
        if fsckpass is None:
            # This is already set by defaults in input.xml, but
            # we're being extra paranoid...
            fsckpass = 2  # pragma: no cover

        dbfs = Filesystem(name=filesystem,
                          mountpoint=mountpoint,
                          mountoptions=options,
                          mount=bool(bootmount),
                          blockdev=blockdevice,
                          fstype=type,
                          passno=fsckpass,
                          dumpfreq=dumpfreq,
                          comments=comments
                          )

        return add_resource(session, logger, holder, dbfs)
