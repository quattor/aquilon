# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Personality


class ThresholdedPersonality(object):
    def __init__(self, dbpersonality, threshold):
        self.dbpersonality = dbpersonality
        self.threshold = threshold


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
            has_threshold = True
            personality = personality.dbpersonality
        details = [indent + "Personality: %s" % personality.name +
                   " Archetype: %s" % personality.archetype.name]
        details.append(indent + "  Template: %s/personality/%s/config.tpl" %
                       (personality.archetype.name, personality.name))
        if has_threshold:
            details.append(indent + "  Threshold: %s" % threshold)
        for service in personality.services:
            details.append(indent + "  Required Service: %s" % service.name)
        if personality.comments:
            details.append(indent + "  Comments: %s" % personality.comments)
        for cltype, info in personality.cluster_infos.items():
            details.append(indent + "  Extra settings for %s clusters:" % cltype)
            if cltype == "esx":
                details.append(indent + "    VM host capacity function: %s" %
                               info.vmhost_capacity_function)
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
        skeleton.name = str(personality.name)
        self.redirect_proto(personality.archetype, skeleton.archetype)
        # FIXME: Implement required services
        if threshold is not None:
            skeleton.threshold = threshold
        return container


ObjectFormatter.handlers[Personality] = PersonalityFormatter()
ObjectFormatter.handlers[ThresholdedPersonality] = PersonalityFormatter()
ObjectFormatter.handlers[PersonalityList] = PersonalityListFormatter()
