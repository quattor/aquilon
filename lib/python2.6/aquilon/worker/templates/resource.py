# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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

from aquilon.aqdb.model import (Application, Filesystem, Intervention,
                                ResourceGroup, Hostlink, RebootSchedule,
                                RebootIntervention)
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_push)

LOGGER = logging.getLogger('aquilon.server.templates.resource')


class PlenaryResource(Plenary):

    template_type = "structure"

    def __init__(self, dbresource, logger=LOGGER):
        Plenary.__init__(self, dbresource, logger=logger)
        self.type = dbresource.resource_type
        self.name = dbresource.name
        self.plenary_core = dbresource.template_base
        self.plenary_template = "config"

    def body(self, lines):
        fname = "body_%s" % self.type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

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
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "eonid", self.dbobj.eonid)

    def body_hostlink(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "target", self.dbobj.target)
        if self.dbobj.owner_group:
            owner_string = self.dbobj.owner_user + ':' + self.dbobj.owner_group
        else:
            owner_string = self.dbobj.owner_user
        pan_assign(lines, "owner", owner_string)

    def body_intervention(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "start", self.dbobj.start_date.isoformat())
        pan_assign(lines, "expiry", self.dbobj.expiry_date.isoformat())

        if self.dbobj.users:
            pan_assign(lines, "users", self.dbobj.users.split(","))
        if self.dbobj.groups:
            pan_assign(lines, "groups", self.dbobj.groups.split(","))

        if self.dbobj.disabled:
            pan_assign(lines, "disabled", self.dbobj.disabled.split(","))

    def body_reboot_schedule(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "time", self.dbobj.time)
        pan_assign(lines, "week", self.dbobj.week)
        pan_assign(lines, "day", self.dbobj.day)

    def body_resourcegroup(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        for resource in self.dbobj.resources:
            pan_push(lines, "resources/%s" % resource.resource_type,
                     StructureTemplate(resource.template_base + "/config"))

    def body_reboot_iv(self, lines):
        pan_assign(lines, "name", self.dbobj.name)
        pan_assign(lines, "justification", self.dbobj.justification)
        self.body_intervention(lines)


Plenary.handlers[Application] = PlenaryResource
Plenary.handlers[Filesystem] = PlenaryResource
Plenary.handlers[Intervention] = PlenaryResource
Plenary.handlers[ResourceGroup] = PlenaryResource
Plenary.handlers[Hostlink] = PlenaryResource
Plenary.handlers[RebootSchedule] = PlenaryResource
Plenary.handlers[RebootIntervention] = PlenaryResource
