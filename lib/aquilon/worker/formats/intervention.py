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
"""Intervention Resource formatter."""

from calendar import timegm

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Intervention


class InterventionFormatter(ResourceFormatter):

    def extra_details(self, intervention, indent=""):
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
        return details

    def format_proto(self, resource, container):
        skeleton = container.resources.add()
        self.add_resource_data(skeleton, resource)
        skeleton.ivdata.expiry = timegm(resource.expiry_date.utctimetuple())
        skeleton.ivdata.start = timegm(resource.start_date.utctimetuple())
        if resource.users is not None:
            skeleton.ivdata.users = resource.users
        if resource.groups is not None:
            skeleton.ivdata.groups = resource.groups
        skeleton.ivdata.justification = resource.justification
        if resource.disabled is not None:
            skeleton.ivdata.disabled = resource.disabled

ObjectFormatter.handlers[Intervention] = InterventionFormatter()
