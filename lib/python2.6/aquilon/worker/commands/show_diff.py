# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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


from aquilon.worker.formats.parameter import DiffData
from aquilon.aqdb.model import (Parameter, Personality,
                                PersonalityServiceMap)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import get_parameters
from collections import defaultdict

class CommandShowDiff(BrokerCommand):

    required_parameters = ["archetype", "personality", "other"]

    def render(self, session, archetype, personality, other,
               other_archetype, **arguments):

        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        if not other_archetype:
            other_archetype = archetype

        db_other_persona = Personality.get_unique(session, name=other,
                                           archetype=other_archetype, compel=True)

        ret = defaultdict(dict)
        self.populate_data(session, dbpersona, "my", ret)
        self.populate_data(session, db_other_persona, "other", ret)

        return DiffData(dbpersona, db_other_persona, ret)

    def populate_data(self, session, dbpersona, dtype, ret):
        """ pouplate data we are interesetd in seeing as part of diff """

        ## parameters
        params = {}

        dbpersona_parameters = get_parameters (session, personality=dbpersona)

        for param in dbpersona_parameters:
            params.update(Parameter.flatten(param.value))
        ret["Parameters"][dtype] =  params

        ## process features
        features = dict((fl.feature.name, True) for fl in dbpersona.features)
        ret["Features"][dtype] =  features

        ## process required_services
        services = dict((srv.name, True) for srv in dbpersona.services)
        ret["Required Services"][dtype] = services

        ## service maps
        q = session.query(PersonalityServiceMap).filter_by(personality=dbpersona)

        smaps = dict(("{0} {1}".format(sm.service_instance, sm.location), True) for sm in q.all())

        ret["ServiceMap"][dtype] = smaps

        ## grns
        grns = dict((grn, True) for grn in dbpersona.grns)
        ret["Grns"][dtype] = grns

        ## options
        enabled = defaultdict()
        if dbpersona.config_override:
            enabled["ConfigOverride"] = True
        if dbpersona.cluster_required:
            enabled["Cluster Required"] = True

        ret["Options Enabled"][dtype] = enabled
