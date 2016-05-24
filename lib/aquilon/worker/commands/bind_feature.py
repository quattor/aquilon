# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import or_

from aquilon.exceptions_ import (ArgumentError, InternalError,
                                 AuthorizationException, UnimplementedError)
from aquilon.aqdb.model import (Feature, Archetype, Personality,
                                PersonalityStage, Model, Domain,
                                CompileableMixin)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import (validate_justification,
                                                         validate_prod_personality)
from aquilon.worker.dbwrappers.feature import add_link, check_feature_template
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandBindFeature(BrokerCommand):

    required_parameters = ['feature']

    def render(self, session, logger, feature, archetype, personality,
               personality_stage, model, vendor, interface, justification,
               reason, user, **_):

        # Binding a feature to a named interface makes sense in the scope of a
        # personality, but not for a whole archetype.
        if interface and not personality:
            raise ArgumentError("Binding to a named interface needs "
                                "a personality.")

        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        else:
            dbarchetype = None

        feature_type = "host"

        # Warning: order matters here!
        params = {}
        if personality:
            dbpersonality = Personality.get_unique(session,
                                                   name=personality,
                                                   archetype=dbarchetype,
                                                   compel=True)
            if not dbarchetype:
                dbarchetype = dbpersonality.archetype
            dbstage = dbpersonality.active_stage(personality_stage)

            personalities = [dbstage]

            params["personality_stage"] = dbstage
            if interface:
                params["interface_name"] = interface
                feature_type = "interface"
        elif archetype:
            params["archetype"] = dbarchetype

            q = session.query(PersonalityStage)
            q = q.join(Personality)
            q = q.options(contains_eager('personality'))
            q = q.filter_by(archetype=dbarchetype)
            personalities = q.all()
        else:
            # It's highly unlikely that a feature template would work for
            # _any_ archetype, so disallow this case for now. As I can't
            # rule out that such a case will not have some uses in the
            # future, the restriction is here and not in the model.
            raise ArgumentError("Please specify either an archetype or "
                                "a personality when binding a feature.")

        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)

            if dbmodel.model_type.isNic():
                feature_type = "interface"
            else:
                feature_type = "hardware"

            params["model"] = dbmodel

        if dbarchetype and not dbarchetype.is_compileable:
            raise UnimplementedError("Binding features to non-compilable "
                                     "archetypes is not implemented.")

        if not feature_type:  # pragma: no cover
            raise InternalError("Feature type is not known.")

        dbfeature = Feature.get_unique(session, name=feature,
                                       feature_type=feature_type, compel=True)

        if personality:
            if dbpersonality.owner_grn != dbfeature.owner_grn and \
               dbfeature.visibility == 'owner_only':
                if not justification:
                    raise AuthorizationException("Changing feature bindings for "
                                                 "a owner_only feature where owner grns "
                                                 "do not match requires --justification.")
                validate_justification(user, justification, reason)
            else:
                validate_prod_personality(dbstage, user, justification, reason)
        else:
            if personalities and not justification:
                raise AuthorizationException("Changing feature bindings for "
                                             "more than just a personality "
                                             "requires --justification.")
            validate_justification(user, justification, reason)

        self.do_link(session, logger, dbfeature, params)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.extend(map(Plenary.get_plenary, personalities))

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
