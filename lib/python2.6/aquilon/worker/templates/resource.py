# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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


import os
import logging

from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.panutils import pan

LOGGER = logging.getLogger('aquilon.server.templates.resource')

class PlenaryResource(Plenary):
    def __init__(self, dbresource, logger=LOGGER):
        Plenary.__init__(self, dbresource, logger=logger)
        self.type = dbresource.resource_type
        self.resource = dbresource
        self.name = dbresource.name
        self.plenary_core = dbresource.template_base
        self.plenary_template = self.plenary_core + "/config"
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        fname = "body_%s" % self.type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_filesystem(self, lines):
        lines.append('"type" = %s;' % pan(self.resource.fstype))
        lines.append('"mountpoint" = %s;' % pan(self.resource.mountpoint))
        lines.append('"mount" = %s;' % pan(self.resource.mount))
        lines.append('"block_device_path" = %s;' % pan(self.resource.blockdev))
        opts = ""
        if self.resource.mountoptions:
            opts = self.resource.mountoptions
        lines.append('"mountopts" = %s;' % pan(opts))
        lines.append('"freq" = %s;' % pan(self.resource.dumpfreq))
        lines.append('"pass" = %s;' % pan(self.resource.passno))

    def body_application(self, lines):
        lines.append('"name" = %s;' % pan(self.resource.name))
        lines.append('"eonid" = %s;' % pan(self.resource.eonid))

    def body_intervention(self, lines):
        lines.append('"expiry" = %s;' %
                     pan(self.resource.expiry_date.isoformat()))

        if self.resource.users:
            lines.append('"users" = %s;' %
                         pan(self.resource.users.split(",")))
        if self.resource.groups:
            lines.append('"groups" = %s;' %
                         pan(self.resource.groups.split(",")))

        if self.resource.disabled:
            lines.append('"disabled" = %s;' %
                         pan(self.resource.disabled.split(",")))
