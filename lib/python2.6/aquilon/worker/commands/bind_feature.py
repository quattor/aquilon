# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from aquilon.exceptions_ import (ArgumentError, PartialError, IncompleteError,
                                 InternalError, AuthorizationException,
                                 UnimplementedError)
from aquilon.aqdb.model import Feature, Archetype, Personality, Model
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.personality import PlenaryPersonality
from aquilon.worker.commands.deploy import validate_justification
from aquilon.worker.dbwrappers.feature import add_link


class CommandBindFeature(BrokerCommand):

    required_parameters = ['feature']

    def render(self, session, logger, feature, archetype, personality, model,
               vendor, interface, justification, user, **arguments):

        # Binding a feature to a named interface makes sense in the scope of a
        # personality, but not for a whole archetype.
        if interface and not personality:
            raise ArgumentError("Binding to a named interface needs "
                                "a personality.")

        q = session.query(Personality)
        dbarchetype = None

        feature_type = "host"

        justification_required = True

        # Warning: order matters here!
        params = {}
        if personality:
            justification_required = False
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

            if dbmodel.machine_type == "nic":
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
        if justification_required and cnt > 0:
            if not justification:
                raise AuthorizationException(
                      "Changing feature bindings for more "
                      "than just a personality requires --justification.")
            validate_justification(user, justification)

        self.do_link(session, logger, dbfeature, params)
        session.flush()

        idx = 0
        written = 0
        successful = []
        failed = []

        with CompileKey(logger=logger):
            personalities = q.all()

            for personality in personalities:
                idx += 1
                if idx % 1000 == 0:  # pragma: no cover
                    logger.client_info("Processing personality %d of %d..." %
                                       (idx, cnt))

                if not personality.archetype.is_compileable:  # pragma: no cover
                    continue

                try:
                    plenary_personality = PlenaryPersonality(personality)
                    written += plenary_personality.write(locked=True)
                    successful.append(plenary_personality)
                except IncompleteError:
                    pass
                except Exception, err:  # pragma: no cover
                    failed.append("{0} failed: {1}".format(personality, err))

            if failed:  # pragma: no cover
                for plenary in successful:
                    plenary.restore_stash()
                raise PartialError([], failed)

        logger.client_info("Flushed %d/%d templates." %
                           (written, written + len(failed)))

        return

    def do_link(self, session, logger, dbfeature, params):
        add_link(session, logger, dbfeature, params)
