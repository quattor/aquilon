# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Personality formatter """


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.cfg import Personality


class PersonalityFormatter(ObjectFormatter):
    def format_raw(self, personality, indent=""):
        details = [ indent + "Personality: %s" % personality.name +
                   " Archetype: %s" % personality.archetype.name ]
        details.append(indent + "    Template: personality/%s" % personality.name)
        for item in personality.service_list:
            details.append(indent + "  Required Service: %s"
                    % item.service.name)
            if item.comments:
                details.append(indent + "    Comments: %s" % item.comments)
        if personality.comments:
            details.append(indent + "  Comments: %s" % personality.comments)
        return "\n".join(details)
#TODO a protocol buffer format
ObjectFormatter.handlers[Personality] = PersonalityFormatter()
