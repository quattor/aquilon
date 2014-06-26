# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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

from aquilon.exceptions_ import (ArgumentError, InternalError,
                                 AuthorizationException, UnimplementedError)
from aquilon.aqdb.model import Feature, Archetype, Personality, Model
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.deploy import validate_justification
from aquilon.worker.dbwrappers.feature import add_link
from aquilon.worker.dbwrappers.personality import validate_personality_justification
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandBindFeature(BrokerCommand):

    required_parameters = ['feature']

    def render(self, session, logger, feature, archetype, personality, model,
               vendor, interface, justification, reason, user, **arguments):

        # Binding a feature to a named interface makes sense in the scope of a
        # personality, but not for a whole archetype.
        if interface and not personality:
            raise ArgumentError("Binding to a named interface needs "
                                "a personality.")

        q = session.query(Personality)
        dbarchetype = None

        feature_type = "host"

        # Warning: order matters here!
        params = {}
        if personality:
            dbpersonality = Personality.get_unique(session,
                                                   name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            params["personality"] = dbpersonality
            if interface:
                params["interface_name"] = interface
                feature_type = "interface"
            dbarchetype = dbpersonality.archetype
            q = q.filter_by(archetype=dbarchetype)
            q = q.filter_by(name=personality)
        elif archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            params["archetype"] = dbarchetype
            q = q.filter_by(archetype=dbarchetype)
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

        cnt = q.count()
        # TODO: should the limit be configurable?
        if personality:
            validate_personality_justification(dbpersonality, user,
                                               justification, reason)
        elif cnt > 0:
            if not justification:
                raise AuthorizationException("Changing feature bindings for "
                                             "more than just a personality "
                                             "requires --justification.")
            validate_justification(user, justification, reason)

        self.do_link(session, logger, dbfeature, params)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        for dbpersonality in q:
            plenaries.append(Plenary.get_plenary(dbpersonality))

        written = plenaries.write()
        logger.client_info("Flushed %d/%d templates." %
                           (written, len(plenaries.plenaries)))
        return

    def do_link(self, session, logger, dbfeature, params):
        add_link(session, logger, dbfeature, params)
