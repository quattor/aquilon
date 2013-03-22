# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
""" Personality formatter """

from aquilon.aqdb.model import Personality
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.worker.templates.base import TEMPLATE_EXTENSION


class ThresholdedPersonality(object):
    def __init__(self, dbpersonality, thresholds):
        self.dbpersonality = dbpersonality
        if not thresholds:
            thresholds = {}
        self.threshold = thresholds.get('threshold')
        self.maintenance_threshold = thresholds.get('maintenance_threshold')


class PersonalityList(list):
    """Holds instances of ThresholdedPersonality."""


class PersonalityListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, tpl, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].PersonalityList()
        for personality in tpl:
            self.redirect_proto(personality, skeleton.personalities.add())
        return skeleton


class PersonalityFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, personality, indent=""):
        # Transparently handle Personality and ThresholdedPersonality
        has_threshold = False
        if hasattr(personality, "dbpersonality"):
            threshold = personality.threshold
            maintenance_threshold = personality.maintenance_threshold
            has_threshold = True
            personality = personality.dbpersonality
        description = "Host"
        if personality.is_cluster:
            description = "Cluster"
        details = [indent + "%s Personality: %s" % (description,
                                                    personality) +
                   " Archetype: %s" % personality.archetype]
        details.append(indent +
                       "  Environment: %s" % personality.host_environment)
        details.append(indent + "  Owned by {0:c}: {0.grn}"
                       .format(personality.owner_grn))
        for grn in personality.grns:
            details.append(indent + "  Used by {0:c}: {0.grn}".format(grn))

        if personality.config_override:
            details.append(indent + "  Config override: enabled")

        details.append(indent + "  Template: %s/personality/%s/config%s" %
                       (personality.archetype, personality, TEMPLATE_EXTENSION))

        if has_threshold:
            details.append(indent + "  Threshold: %s" % threshold)
            details.append(indent + "  Maintenance Threshold: %s" %
                           maintenance_threshold)
        if personality.cluster_required:
            details.append(indent + "  Requires clustered hosts")
        for service in personality.services:
            details.append(indent + "  Required Service: %s" % service.name)

        features = personality.features[:]
        features.sort(key=lambda x: (x.feature.feature_type,
                                     x.feature.post_personality,
                                     x.feature.name))

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
                details.append(indent + "    Interface: %s" %
                               link.interface_name)

        if personality.comments:
            details.append(indent + "  Comments: %s" % personality.comments)

        for cltype, info in personality.cluster_infos.items():
            details.append(indent + "  Extra settings for %s clusters:" % cltype)
            if cltype == "esx":
                details.append(indent + "    VM host capacity function: %s" %
                               info.vmhost_capacity_function)
                details.append(indent + "    VM host overcommit factor: %s" %
                               info.vmhost_overcommit_memory)
        return "\n".join(details)

    def format_proto(self, personality, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].PersonalityList()
            skeleton = container.personalities.add()
        # Transparently handle Personality and ThresholdedPersonality
        threshold = None
        if hasattr(personality, "dbpersonality"):
            threshold = personality.threshold
            personality = personality.dbpersonality

        self.add_personality_data(skeleton, personality)
        if threshold is not None:
            skeleton.threshold = threshold

        if personality.grns:
            skeleton.owner_eonid = personality.grns[0].eon_id

        features = personality.features[:]
        features.sort(key=lambda x: (x.feature.feature_type,
                                     x.feature.post_personality,
                                     x.feature.name))

        for link in features:
            self.add_featurelink_msg(skeleton.features.add(), link)

        for service in personality.services:
            rsvc_msg = skeleton.required_services.add()
            rsvc_msg.service = service.name

        if personality.comments:
            skeleton.comments = personality.comments

        skeleton.config_override = personality.config_override
        skeleton.cluster_required = personality.cluster_required

        return container


ObjectFormatter.handlers[Personality] = PersonalityFormatter()
ObjectFormatter.handlers[ThresholdedPersonality] = PersonalityFormatter()
ObjectFormatter.handlers[PersonalityList] = PersonalityListFormatter()
