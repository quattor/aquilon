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
from aquilon.worker.templates.panutils import pan, StructureTemplate

LOGGER = logging.getLogger('aquilon.server.templates.resource')


class PlenaryResource(Plenary):
    def __init__(self, dbresource, logger=LOGGER):
        Plenary.__init__(self, dbresource, logger=logger)
        self.type = dbresource.resource_type
        self.name = dbresource.name
        self.plenary_core = dbresource.template_base
        self.plenary_template = self.plenary_core + "/config"
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        fname = "body_%s" % self.type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_filesystem(self, lines):
        lines.append('"type" = %s;' % pan(self.dbobj.fstype))
        lines.append('"mountpoint" = %s;' % pan(self.dbobj.mountpoint))
        lines.append('"mount" = %s;' % pan(self.dbobj.mount))
        lines.append('"block_device_path" = %s;' % pan(self.dbobj.blockdev))
        opts = ""
        if self.dbobj.mountoptions:
            opts = self.dbobj.mountoptions
        lines.append('"mountopts" = %s;' % pan(opts))
        lines.append('"freq" = %s;' % pan(self.dbobj.dumpfreq))
        lines.append('"pass" = %s;' % pan(self.dbobj.passno))

    def body_application(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        lines.append('"eonid" = %s;' % pan(self.dbobj.eonid))

    def body_hostlink(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        lines.append('"target" = %s;' % pan(self.dbobj.target))
        owner_string = '"owner" = %s;'
        if self.dbobj.owner_group:
            lines.append(owner_string % pan(self.dbobj.owner_user + ':' +
                                            self.dbobj.owner_group))
        else:
            lines.append(owner_string % pan(self.dbobj.owner_user))

    def body_intervention(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        lines.append('"start" = %s;' %
                     pan(self.dbobj.start_date.isoformat()))
        lines.append('"expiry" = %s;' %
                     pan(self.dbobj.expiry_date.isoformat()))

        if self.dbobj.users:
            lines.append('"users" = %s;' %
                         pan(self.dbobj.users.split(",")))
        if self.dbobj.groups:
            lines.append('"groups" = %s;' %
                         pan(self.dbobj.groups.split(",")))

        if self.dbobj.disabled:
            lines.append('"disabled" = %s;' %
                         pan(self.dbobj.disabled.split(",")))

    def body_reboot_schedule(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        lines.append('"time" = %s;' % pan(self.dbobj.time))
        lines.append('"week" = %s;' % pan(self.dbobj.week))
        lines.append('"day" = %s;' % pan(self.dbobj.day))

    def body_resourcegroup(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        for resource in self.dbobj.resources:
            lines.append('"resources/%s" = push(%s);' %
                         (resource.resource_type,
                          pan(StructureTemplate(resource.template_base +
                                                "/config"))))

    def body_reboot_iv(self, lines):
        lines.append('"name" = %s;' % pan(self.dbobj.name))
        lines.append('"justification" = %s;' % pan(self.dbobj.justification))
        self.body_intervention(lines)


Plenary.handlers[Application] = PlenaryResource
Plenary.handlers[Filesystem] = PlenaryResource
Plenary.handlers[Intervention] = PlenaryResource
Plenary.handlers[ResourceGroup] = PlenaryResource
Plenary.handlers[Hostlink] = PlenaryResource
Plenary.handlers[RebootSchedule] = PlenaryResource
Plenary.handlers[RebootIntervention] = PlenaryResource
