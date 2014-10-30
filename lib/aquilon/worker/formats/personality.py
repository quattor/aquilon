# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
""" Personality formatter """

from operator import attrgetter

from aquilon.aqdb.model import Personality
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


class PersonalityFormatter(ObjectFormatter):
    def format_raw(self, personality, indent=""):
        description = "Host"
        if personality.is_cluster:
            description = "Cluster"
        details = [indent + "{0} Personality: {1.name} Archetype: {1.archetype.name}"
                   .format(description, personality)]
        details.append(indent + "  Environment: {0.name}"
                       .format(personality.host_environment))
        details.append(indent + "  Owned by {0:c}: {0.grn}"
                       .format(personality.owner_grn))
        for grn_rec in sorted(personality.grns, key=attrgetter("target", "eon_id")):
            details.append(indent + "  Used by {0.grn:c}: {0.grn.grn} "
                           "[target: {0.target}]".format(grn_rec))

        if personality.config_override:
            details.append(indent + "  Config override: enabled")

        details.append(indent + "  Template: {0.archetype.name}/personality/{0.name}/config"
                       .format(personality))

        if personality.cluster_required:
            details.append(indent + "  Requires clustered hosts")
        for service in personality.services:
            details.append(indent + "  Required Service: {0.name}"
                           .format(service))

        for usr in personality.root_users:
            details.append(indent + "  Root Access User: %s" % usr)

        for ng in personality.root_netgroups:
            details.append(indent + "  Root Access Netgroup: %s" % ng)

        features = personality.features[:]
        features.sort(key=attrgetter("feature.feature_type",
                                     "feature.post_personality",
                                     "feature.name"))

        for link in features:
            if link.feature.post_personality:
                flagstr = " [post_personality]"
            elif link.feature.post_personality_allowed:
                flagstr = " [pre_personality]"
            else:
                flagstr = ""

            details.append(indent + "  {0:c}: {0.name}{1}"
                           .format(link.feature, flagstr))
            if link.model:
                details.append(indent + "    {0:c}: {0.name} {1:c}: {1.name}"
                               .format(link.model.vendor, link.model))
            if link.interface_name:
                details.append(indent + "    Interface: {0.interface_name}"
                               .format(link))

        if personality.comments:
            details.append(indent + "  Comments: {0.comments}"
                           .format(personality))

        for cltype, info in personality.cluster_infos.items():
            details.append(indent + "  Extra settings for %s clusters:" % cltype)
            if cltype == "esx":
                details.append(indent + "    VM host capacity function: %s" %
                               info.vmhost_capacity_function)
                details.append(indent + "    VM host overcommit factor: %s" %
                               info.vmhost_overcommit_memory)
        return "\n".join(details)

    def fill_proto(self, personality, skeleton):
        skeleton.name = str(personality)
        for service in personality.services:
            si = skeleton.required_services.add()
            si.service = service.name

        self.redirect_proto(personality.archetype, skeleton.archetype)
        skeleton.host_environment = str(personality.host_environment)
        skeleton.owner_eonid = personality.owner_eon_id

        features = personality.features[:]
        features.sort(key=attrgetter("feature.feature_type",
                                     "feature.post_personality",
                                     "feature.name"))

        for link in features:
            feat_msg = skeleton.features.add()
            self.redirect_proto(link.feature, feat_msg)
            if link.model:
                self.redirect_proto(link.model, feat_msg.model)
            if link.interface_name:
                feat_msg.interface_name = str(link.interface_name)

        if personality.comments:
            skeleton.comments = personality.comments

        skeleton.config_override = personality.config_override
        skeleton.cluster_required = personality.cluster_required
        for grn_rec in sorted(personality.grns,
                              key=attrgetter("target", "eon_id")):
            map = skeleton.eonid_maps.add()
            map.target = grn_rec.target
            map.eonid = grn_rec.eon_id

ObjectFormatter.handlers[Personality] = PersonalityFormatter()


class SimplePersonalityList(list):
    """Holds a list of personalities for which a list will be formatted
       in a simple (name-only) manner."""


class SimplePersonalityListFormatter(ListFormatter):
    def format_raw(self, result, indent=""):
        return str("\n".join([indent + "{0.archetype.name}/{0.name}".format(obj) for obj in result]))

    def csv_fields(self, obj):
        yield (obj.archetype.name, obj.name,)

    def fill_proto(self, personality, skeleton):
        skeleton.name = str(personality)
        skeleton.archetype.name = str(personality.archetype.name)
        skeleton.host_environment = str(personality.host_environment)
        skeleton.owner_eonid = personality.owner_eon_id

ObjectFormatter.handlers[SimplePersonalityList] = SimplePersonalityListFormatter()
