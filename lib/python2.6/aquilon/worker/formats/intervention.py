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
"""Intervention Resource formatter."""

from calendar import timegm

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Intervention


class InterventionFormatter(ResourceFormatter):

    def format_raw(self, intervention, indent=""):
        details = []
        details.append("  Start: %s" % intervention.start_date)
        details.append("  Expires: %s" % intervention.expiry_date)
        details.append("  Justification: %s" % intervention.justification)
        if intervention.users:
            details.append("  Allow Users: %s" % intervention.users)
        if intervention.groups:
            details.append("  Allow Groups: %s" % intervention.groups)
        if intervention.disabled:
            details.append("  Disabled Actions: %s" % intervention.disabled)
        return super(InterventionFormatter, self).format_raw(intervention,
                                                             indent) + \
               "\n" + "\n".join(details)

    def format_proto(self, resource, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        skeleton.ivdata.expiry = timegm(resource.expiry_date.utctimetuple())
        skeleton.ivdata.start = timegm(resource.start_date.utctimetuple())
        if resource.users is not None:
            skeleton.ivdata.users = resource.users
        if resource.groups is not None:
            skeleton.ivdata.groups = resource.groups
        skeleton.ivdata.justification = resource.justification
        if resource.disabled is not None:
            skeleton.ivdata.disabled = resource.disabled
        return super(InterventionFormatter, self).format_proto(resource,
                                                               skeleton)


ObjectFormatter.handlers[Intervention] = InterventionFormatter()

