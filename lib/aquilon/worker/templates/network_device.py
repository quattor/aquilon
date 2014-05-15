# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

import re
import logging

from sqlalchemy.inspection import inspect

from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      add_location_info)
from aquilon.worker.templates.panutils import pan, pan_assign, pan_include
from aquilon.aqdb.model import NetworkDevice
from aquilon.utils import nlist_key_re


LOGGER = logging.getLogger(__name__)


class PlenaryNetworkDeviceInfo(StructurePlenary):

    @classmethod
    def template_name(cls, dbmachine):
        loc = dbmachine.location
        return "network_device/%s/%s/%s" % (loc.hub.fullname.lower(),
                                            loc.building, dbmachine.label)

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            # TODO: this should become a CompileKey if we start generating
            # profiles for switches (see also templates/cluster.py)
            return PlenaryKey(network_device=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

    def body(self, lines):
        pan_assign(lines, "nodename", self.dbobj.label)
        if self.dbobj.serial_no:
            pan_assign(lines, "serialnumber", self.dbobj.serial_no)
        lines.append("")

        pan_assign(lines, "model_type", self.dbobj.model.model_type)
        pan_include(lines, "hardware/network_device/%s/%s" %
                    (self.dbobj.model.vendor.name, self.dbobj.model.name))
        lines.append("")

        add_location_info(lines, self.dbobj.location)
        lines.append("")

        interfaces = {}
        for interface in self.dbobj.interfaces:
            ifinfo = {}
            ifinfo["type"] = interface.interface_type
            if interface.mac:
                ifinfo["hwaddr"] = interface.mac
            interfaces[interface.name] = ifinfo
        for name in sorted(interfaces.keys()):
            # This is ugly. We can't blindly escape, because that would affect
            # e.g. VLAN interfaces. Calling unescape() for a non-escaped VLAN
            # interface name is safe though, so we can hopefully get rid of this
            # once the templates are changed to call unescape().
            if nlist_key_re.match(name):
                pan_assign(lines, "cards/nic/%s" % name,
                           interfaces[name])
            else:
                pan_assign(lines, "cards/nic/{%s}" % name,
                           interfaces[name])
        lines.append("")


Plenary.handlers[NetworkDevice] = PlenaryNetworkDeviceInfo


