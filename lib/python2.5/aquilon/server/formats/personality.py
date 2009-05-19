# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Personality formatter """


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.cfg import Personality


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
        details = [ indent + "Personality: %s" % personality.name +
                   " Archetype: %s" % personality.archetype.name ]
        details.append(indent + "  Template: %s/personality/%s/config.tpl" %
                       (personality.archetype.name, personality.name))
        if has_threshold:
            details.append(indent + "  Threshold: %s" % threshold)
        for item in personality.service_list:
            details.append(indent + "  Required Service: %s"
                    % item.service.name)
            if item.comments:
                details.append(indent + "    Comments: %s" % item.comments)
        if personality.comments:
            details.append(indent + "  Comments: %s" % personality.comments)
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
        if threshold:
            skeleton.threshold = threshold
        return container


ObjectFormatter.handlers[Personality] = PersonalityFormatter()
ObjectFormatter.handlers[ThresholdedPersonality] = PersonalityFormatter()
ObjectFormatter.handlers[PersonalityList] = PersonalityListFormatter()


