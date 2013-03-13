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
"""Contains the logic for `aq show personality`."""


import os
import re

from sqlalchemy.orm import joinedload, subqueryload, contains_eager

from aquilon.aqdb.model import Archetype, Personality
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.personality import (ThresholdedPersonality,
                                                PersonalityList)
from aquilon.worker.dbwrappers.branch import get_branch_and_author


class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, logger,
               personality, archetype, domain, sandbox, **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox)
        if archetype and personality:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            if not dbbranch:
                return dbpersonality
            thresholds = self.get_threshold(dbpersonality, dbbranch, dbauthor)
            return ThresholdedPersonality(dbpersonality, thresholds)
        q = session.query(Personality)
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            q = q.filter_by(archetype=dbarchetype)
        if personality:
            q = q.filter_by(name=personality)
        q = q.join(Archetype)
        q = q.order_by(Archetype.name, Personality.name)
        q = q.options(contains_eager('archetype'),
                      subqueryload('services'),
                      subqueryload('grns'),
                      subqueryload('features'),
                      joinedload('features.feature'),
                      joinedload('cluster_infos'))
        results = PersonalityList()
        if not dbbranch:
            results.extend(q.all())
            return results
        for dbpersonality in q.all():
            # In theory the results here could be inconsistent if the
            # domain is being written to.  In practice... it's not worth
            # taking out the compile lock to ensure consistency.
            thresholds = self.get_threshold(dbpersonality, dbbranch, dbauthor)
            results.append(ThresholdedPersonality(dbpersonality, thresholds))
        return results

    threshold_re = re.compile(r'^\s*"((?:maintenance_)?threshold)"\s*='
                              r'\s*(\d+)\s*;\s*$', re.M)

    def get_threshold(self, dbpersonality, dbbranch, dbauthor):
        if dbbranch.branch_type == 'sandbox':
            domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                                     dbauthor.name, dbbranch.name)
        else:
            domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                     dbbranch.name)
        template = os.path.join(domaindir, dbpersonality.archetype.name,
                                "personality", dbpersonality.name,
                                "espinfo.tpl")
        try:
            contents = open(template).read()
        except IOError:
            return None
        values = dict(threshold=None, maintenance_threshold=None)
        for m in self.threshold_re.finditer(contents):
            values[m.group(1)] = int(m.group(2))
        return values
