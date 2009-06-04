# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.model import Personality
from aquilon.server.formats.personality import (ThresholdedPersonality,
                                                PersonalityList)
from aquilon.server.dbwrappers.domain import get_domain


class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, personality, archetype, domain, **arguments):
        if domain:
            dbdomain = get_domain(session, domain)
        if archetype and personality:
            dbpersonality = get_personality(session, archetype, personality)
            if not domain:
                return dbpersonality
            threshold = self.get_threshold(dbpersonality, dbdomain)
            return ThresholdedPersonality(dbpersonality, threshold)
        q = session.query(Personality)
        if archetype:
            dbarchetype = get_archetype(session, archetype)
            q = q.filter_by(archetype=dbarchetype)
        if personality:
            q = q.filter_by(name=personality)
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


