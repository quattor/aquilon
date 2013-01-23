# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.panutils import pan
from aquilon.aqdb.model import Switch


LOGGER = logging.getLogger(__name__)


class PlenarySwitch(Plenary):

    template_type = ""

    """
    A facade for the variety of PlenarySwitch subsidiary files
    """

    def __init__(self, dbswitch, logger=LOGGER):
        Plenary.__init__(self, dbswitch, logger=logger)
        self.dbobj = dbswitch
        self.name = str(dbswitch.primary_name)
        self.plenary_core = "switchdata"
        self.plenary_template = self.name

    def body(self, lines):

        vlans = {}
        for ov in self.dbobj.observed_vlans:
            vlan = {}

            vlan["vlanid"] = pan(ov.vlan.vlan_id)
            vlan["network_ip"] = ov.network.ip
            vlan["netmask"] = ov.network.netmask
            vlan["network_type"] = ov.network.network_type
            vlan["network_environment"] = ov.network.network_environment.name

            vlans[ov.vlan.port_group] = vlan

        lines.append('"/system/network/vlans" = %s;' % pan(vlans))

Plenary.handlers[Switch] = PlenarySwitch

