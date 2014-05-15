# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Feature formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (Feature, HostFeature, HardwareFeature,
                                InterfaceFeature)

import json

class FeatureFormatter(ObjectFormatter):

    def format_raw(self, feature, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(feature))
        if feature.post_personality_allowed:
            details.append(indent + "  Post Personality: %s" %
                           feature.post_personality)
        details.append(indent + "  Template: %s" % feature.cfg_path)

        for link in feature.links:
            opts = []
            if link.model:
                opts.append(format(link.model))
            if link.archetype:
                opts.append(format(link.archetype))
            if link.personality:
                opts.append(format(link.personality))
            if link.interface_name:
                opts.append("Interface %s" % link.interface_name)

            details.append(indent + "  Bound to: %s" % ", ".join(opts))

        if feature.comments:
            details.append(indent + "  Comments: %s" % feature.comments)

        return "\n".join(details)


    def format_json(self, feature):
        result = {
            feature.__class__.__name__ : feature.name,
            "Comments" : feature.comments
        }

        return json.dumps(result)

ObjectFormatter.handlers[Feature] = FeatureFormatter()
ObjectFormatter.handlers[HostFeature] = FeatureFormatter()
ObjectFormatter.handlers[HardwareFeature] = FeatureFormatter()
ObjectFormatter.handlers[InterfaceFeature] = FeatureFormatter()
