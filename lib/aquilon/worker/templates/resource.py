# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from aquilon.aqdb.model import (Application, Filesystem, Intervention,
                                ResourceGroup, Hostlink, RebootSchedule,
                                RebootIntervention, ServiceAddress,
                                VirtualMachine, Share)
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      PlenaryCollection)
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_append)

LOGGER = logging.getLogger('aquilon.server.templates.resource')


class PlenaryResource(StructurePlenary):

    def __init__(self, dbresource, logger=LOGGER):
        super(PlenaryResource, self).__init__(dbresource, logger=logger)

        self.type = dbresource.resource_type
        self.name = dbresource.name
        self.plenary_core = dbresource.template_base
        self.plenary_template = "config"

    def body(self, lines):
        pan_assign(lines, "name", self.name)

        fname = "body_%s" % self.type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_share(self, lines):
        pan_assign(lines, "server", self.dbobj.server)
        pan_assign(lines, "mountpoint", self.dbobj.mount)

    def body_filesystem(self, lines):
        pan_assign(lines, "type", self.dbobj.fstype)
        pan_assign(lines, "mountpoint", self.dbobj.mountpoint)
        pan_assign(lines, "mount", self.dbobj.mount)
        pan_assign(lines, "block_device_path", self.dbobj.blockdev)
        opts = ""
        if self.dbobj.mountoptions:
            opts = self.dbobj.mountoptions
        pan_assign(lines, "mountopts", opts)
        pan_assign(lines, "freq", self.dbobj.dumpfreq)
        pan_assign(lines, "pass", self.dbobj.passno)

    def body_application(self, lines):
        pan_assign(lines, "eonid", self.dbobj.eonid)

    def body_hostlink(self, lines):
        pan_assign(lines, "target", self.dbobj.target)
        if self.dbobj.owner_group:
            owner_string = self.dbobj.owner_user + ':' + self.dbobj.owner_group
        else:
            owner_string = self.dbobj.owner_user
        pan_assign(lines, "owner", owner_string)

    def body_intervention(self, lines):
        pan_assign(lines, "start", self.dbobj.start_date.isoformat())
        pan_assign(lines, "expiry", self.dbobj.expiry_date.isoformat())

        if self.dbobj.users:
            pan_assign(lines, "users", self.dbobj.users.split(","))
        if self.dbobj.groups:
            pan_assign(lines, "groups", self.dbobj.groups.split(","))

        if self.dbobj.disabled:
            pan_assign(lines, "disabled", self.dbobj.disabled.split(","))

    def body_reboot_schedule(self, lines):
        pan_assign(lines, "time", self.dbobj.time)
        pan_assign(lines, "week", self.dbobj.week)
        pan_assign(lines, "day", self.dbobj.day)

    def body_resourcegroup(self, lines):
        if self.dbobj.resholder:
            for resource in self.dbobj.resholder.resources:
                pan_append(lines, "resources/" + resource.resource_type,
                           StructureTemplate(resource.template_base +
                                             "/config"))

    def body_reboot_iv(self, lines):
        pan_assign(lines, "justification", self.dbobj.justification)
        self.body_intervention(lines)

    def body_service_address(self, lines):
        pan_assign(lines, "ip", str(self.dbobj.dns_record.ip))
        pan_assign(lines, "fqdn", str(self.dbobj.dns_record.fqdn))
        pan_assign(lines, "interfaces", self.dbobj.interfaces)

    def body_virtual_machine(self, lines):

        machine = self.dbobj.machine
        pmac = Plenary.get_plenary(machine)
        pan_assign(lines, "hardware",
                   StructureTemplate(pmac.plenary_template_name))

        # One day we may get to the point where this will be required.
        # FIXME: read the data from the host data template
        if (machine.host):
            # we fill this in manually instead of just assigning
            # 'system' = value("hostname:/system")
            # because the target host might not actually have a profile.
            arch = machine.host.archetype
            os = machine.host.operating_system
            pn = machine.primary_name.fqdn

            system = {'archetype': {'name': arch.name,
                                    'os': os.name,
                                    'osversion': os.version},
                      'build': machine.host.status.name,
                      'network': {'hostname': pn.name,
                                  'domainname': pn.dns_domain}}
            pan_assign(lines, "system", system)


Plenary.handlers[Application] = PlenaryResource
Plenary.handlers[Filesystem] = PlenaryResource
Plenary.handlers[Intervention] = PlenaryResource
Plenary.handlers[Hostlink] = PlenaryResource
Plenary.handlers[RebootSchedule] = PlenaryResource
Plenary.handlers[RebootIntervention] = PlenaryResource
Plenary.handlers[ServiceAddress] = PlenaryResource
Plenary.handlers[Share] = PlenaryResource
Plenary.handlers[VirtualMachine] = PlenaryResource


class PlenaryResourceGroup(PlenaryCollection):
    def __init__(self, dbresource, logger=LOGGER):
        super(PlenaryResourceGroup, self).__init__(logger=logger)

        self.dbobj = dbresource
        self.real_plenary = PlenaryResource(dbresource, logger=logger)

        self.plenaries.append(self.real_plenary)
        if dbresource.resholder:
            for res in dbresource.resholder.resources:
                self.plenaries.append(PlenaryResource(res))

    def read(self):
        # This is used by the cat command
        return self.real_plenary.read()

    def _generate_content(self):
        return self.real_plenary._generate_content()


Plenary.handlers[ResourceGroup] = PlenaryResourceGroup
