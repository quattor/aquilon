# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show personality`."""


import os
import re

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.model import Personality
from aquilon.server.formats.personality import (ThresholdedPersonality,
                                                PersonalityList)
from aquilon.server.dbwrappers.domain import get_domain


class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, name, archetype, domain, **arguments):
        if domain:
            dbdomain = get_domain(session, domain)
        if archetype and name:
            dbpersonality = get_personality(session, archetype, name)
            if not domain:
                return dbpersonality
            threshold = self.get_threshold(dbpersonality, dbdomain)
            return ThresholdedPersonality(dbpersonality, threshold)
        q = session.query(Personality)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
            q = q.filter_by(archetype=dbarchetype)
        if name:
            q = q.filter_by(name=name)
        results = PersonalityList()
        if not domain:
            results.extend(q.all())
            return results
        for dbpersonality in q.all():
            threshold = self.get_threshold(dbpersonality, dbdomain)
            results.append(ThresholdedPersonality(dbpersonality, threshold))
        return results

    threshold_re = re.compile(r'^\s*"threshold"\s*=\s*(\d+)\s*;\s*$', re.M)

    def get_threshold(self, dbpersonality, dbdomain):
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        template = os.path.join(domaindir, dbpersonality.archetype.name,
                                "personality", dbpersonality.name,
                                "espinfo.tpl")
        try:
            contents = open(template).read()
        except IOError:
            return None
        m = self.threshold_re.search(contents)
        if not m:
            return None
        return int(m.group(1))


