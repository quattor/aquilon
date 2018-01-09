# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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

from sqlalchemy.sql import or_

from aquilon.exceptions_ import ArgumentError, AuthorizationException
from aquilon.aqdb.model import (HostFeature, HardwareFeature, InterfaceFeature,
                                Archetype, Personality, PersonalityStage, Model,
                                Domain, CompileableMixin)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.feature import (add_link, check_feature_template,
                                               get_affected_plenaries)


class CommandBindFeature(BrokerCommand):
    requires_plenaries = True

    required_parameters = ['feature']

    def render(self, session, logger, plenaries, feature, archetype, personality,
               personality_stage, model, vendor, interface, justification,
               reason, user, **arguments):

        params = {}

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)

        # Step 1: define the target - either a personality or an archetype
        if personality:
            dbpersonality = Personality.get_unique(session,
                                                   name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            dbarchetype = dbpersonality.archetype
            dbstage = dbpersonality.active_stage(personality_stage)
            params["personality_stage"] = dbstage
            # Validate ChangeManagement
            cm.consider(dbstage)
        elif archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            params["archetype"] = dbarchetype
            # Validate ChangeManagement
            cm.consider(dbarchetype)
        else:
            # It's highly unlikely that a feature template would work for
            # _any_ archetype, so disallow this case for now. As I can't
            # rule out that such a case will not have some uses in the
            # future, the restriction is here and not in the model.
            raise ArgumentError("Please specify either an archetype or "
                                "a personality when binding a feature.")

        # Validate ChangeManagement
        cm.validate()

        dbarchetype.require_compileable("feature bindings are not supported")

        # Binding a feature to a named interface makes sense in the scope of a
        # personality, but not for a whole archetype.
        if interface and not personality:
            raise ArgumentError("Binding to a named interface needs "
                                "a personality.")

        # Step 2: parse the modifiers, and identify the feature
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)

            if dbmodel.model_type.isNic():
                feature_cls = InterfaceFeature
            else:
                feature_cls = HardwareFeature

            params["model"] = dbmodel
        else:
            feature_cls = HostFeature
            dbmodel = None

        if interface:
            if dbmodel and not dbmodel.model_type.isNic():
                raise ArgumentError("{0} is not a network interface model."
                                    .format(dbmodel))
            feature_cls = InterfaceFeature
            params["interface_name"] = interface

        dbfeature = feature_cls.get_unique(session, name=feature, compel=True)

        if personality and dbpersonality.owner_grn != dbfeature.owner_grn \
                and dbfeature.visibility == 'owner_only':
            raise ArgumentError("Personality and feature owners do not "
                                "match and feature visibility is set to 'owner_only'.")

        # Step 4: do it
        get_affected_plenaries(session, dbfeature, plenaries, **params)
        self.do_link(session, logger, dbfeature, params)

        session.flush()

        plenaries.write(verbose=True)

    def do_link(self, session, logger, dbfeature, params):
        # Check that the feature templates exist in all affected domains. We
        # don't care about sandboxes, it's the job of sandbox owners to fix
        # them if they break.
        if "personality_stage" in params:
            dbstage = params["personality_stage"]
            dbarchetype = dbstage.archetype
        else:
            dbstage = None
            dbarchetype = params["archetype"]

        filters = []
        for cls_ in CompileableMixin.__subclasses__():
            subq = session.query(cls_.branch_id)
            subq = subq.distinct()

            if dbstage:
                subq = subq.filter_by(personality_stage=dbstage)
            else:
                subq = subq.join(PersonalityStage, Personality)
                subq = subq.filter_by(archetype=dbarchetype)
            filters.append(Domain.id.in_(subq.subquery()))

        q = session.query(Domain)
        q = q.distinct()
        q = q.filter(or_(*filters))

        for dbdomain in q:
            check_feature_template(self.config, dbarchetype, dbfeature,
                                   dbdomain)

        add_link(session, logger, dbfeature, params)
