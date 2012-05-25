# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq show personality`."""


import os
import re

from sqlalchemy.orm import joinedload, subqueryload, contains_eager

from aquilon.aqdb.model import Archetype, Personality
from aquilon.worker.broker import BrokerCommand
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
