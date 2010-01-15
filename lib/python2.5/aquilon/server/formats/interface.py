# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Interface formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Interface


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        details = ''
        if interface.mac:
            details = [indent + "Interface: %s %s boot=%s" % (
                interface.name, interface.mac, interface.bootable)]
        else:
            details = [indent + "Interface: %s boot=%s (no mac addr)" % (
                interface.name, interface.bootable)]

        details.append(indent + "  Type: %s" % interface.interface_type)

        hw = interface.hardware_entity
        hw_type = hw.hardware_entity_type
        if hw_type == 'machine':
            details.append(indent + "  Attached to: machine %s" % hw.name)
        elif hw_type == 'tor_switch_hw':
            if hw.tor_switch:
                details.append(indent + "  Attached to: tor_switch %s" %
                                   ",".join([ts.fqdn for ts in hw.tor_switch]))
            else:
                details.append("  Attached to: unnamed tor_switch")
        elif hw_type == 'chassis_hw':
            if hw.chassis_hw:
                details.append("  Attached to: chassis %s" %
                                   ",".join([c.fqdn for c in hw.chassis_hw]))
            else:
                details.append("  Attached to: unnamed chassis")
        elif getattr(hw, "name", None):
            details.append("  Attached to: %s" % hw.name)
        if interface.system:
            details.append(indent + "  Provides: %s [%s]" %
                           (interface.system.fqdn, interface.system.ip))
        return "\n".join(details)

ObjectFormatter.handlers[Interface] = InterfaceFormatter()


class MissingManagersList(list):
    pass

class MissingManagersFormatter(ObjectFormatter):
    def format_raw(self, mmlist, indent=""):
        commands = []
        for interface in mmlist:
            host = interface.hardware_entity.host
            if host:
                # FIXME: Deal with multiple management interfaces?
                commands.append("aq add manager --hostname '%s' --ip 'IP'" %
                                host.fqdn)
            else:
                commands.append("# No host found for machine %s with management interface" %
                                interface.hardware_entity.name)
        return "\n".join(commands)

    def format_csv(self, mmlist):
        hosts = []
        for interface in mmlist:
            host = interface.hardware_entity.host
            if host:
                # FIXME: Deal with multiple management interfaces?
                hosts.append(host.fqdn)
        return "\n".join(hosts)

ObjectFormatter.handlers[MissingManagersList] = MissingManagersFormatter()
