# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.update_resource import CommandUpdateResource


class CommandUpdateFilesystem(CommandUpdateResource):

    required_parameters = ["filesystem"]
    resource_class = Filesystem
    resource_name = "filesystem"

    def update_resource(self, dbresource, session, logger, type, mountpoint, blockdevice, bootmount, dumpfreq, fsckpass, options, **_):
        if type is not None:
            dbresource.fstype = type

        if mountpoint is not None:
            dbresource.mountpoint = mountpoint

        if blockdevice is not None:
            dbresource.blockdev = blockdevice

        if bootmount is not None:
            dbresource.mount = bool(bootmount)

        if dumpfreq is not None:
            dbresource.dumpfreq = dumpfreq

        if fsckpass is not None:
            dbresource.passno = fsckpass

        if options is not None:
            dbresource.mountoptions = options
