# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""TorSwitchHw formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import TorSwitchHw, HardwareEntity


class TorSwitchHwFormatter(ObjectFormatter):
    def format_raw(self, tor_switch_hw, indent=""):
        details = []
        for tor_switch in tor_switch_hw.tor_switch:
            details.append(self.redirect_raw(tor_switch, indent))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_raw(tor_switch_hw, indent))
        return "\n".join(details)

    def format_csv(self, tor_switch_hw):
        details = []
        for tor_switch in tor_switch_hw.tor_switch:
            details.append(self.redirect_csv(tor_switch))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_csv(tor_switch_hw))
        return "\n".join(details)

ObjectFormatter.handlers[TorSwitchHw] = TorSwitchHwFormatter()
