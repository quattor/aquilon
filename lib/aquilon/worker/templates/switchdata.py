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

import logging

from sqlalchemy.inspection import inspect

from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates import StructurePlenary
from aquilon.worker.templates.panutils import pan


LOGGER = logging.getLogger(__name__)


class PlenarySwitchData(StructurePlenary):
    """
    A facade for the variety of PlenarySwitchData subsidiary files
    """

    prefix = "switchdata"

    @classmethod
    def template_name(cls, dbhost):
        return cls.prefix + "/" + str(dbhost.fqdn)

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(network_device=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

    def body(self, lines):

        vlans = {}
        for pg in self.dbobj.observed_vlans:
            vlan = {}

            vlan["vlanid"] = pan(pg.network_tag)
            net = pg.network
            vlan["network_ip"] = net.ip
            vlan["netmask"] = net.netmask
            vlan["network_type"] = net.network_type
            vlan["network_environment"] = net.network_environment.name

            vlans[pg.name] = vlan

        lines.append('"system/network/vlans" = %s;' % pan(vlans))
