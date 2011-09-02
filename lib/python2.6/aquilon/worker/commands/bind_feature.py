# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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

from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import or_

from aquilon.exceptions_ import (ArgumentError, NotFoundException, PartialError,
                                 IncompleteError, AuthorizationException,
                                 UnimplementedError)
from aquilon.aqdb.model import (Feature, FeatureLink, Archetype, Personality,
                                Model, Machine, Host, Interface)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.commands.deploy import validate_justification
from aquilon.utils import first_of


class CommandBindFeature(BrokerCommand):

    required_parameters = ['feature']

    def render(self, session, logger, feature, archetype, personality, model,
               vendor, interface, justification, flush, user, **arguments):

        # Binding a feature to a named interface makes sense in the scope of a
        # personality, but not for a whole archetype.
        if interface and not personality:
            raise ArgumentError("Binding to a named interface needs "
                                "a personality.")

        justification_required = False

        q = session.query(Host)
        q = q.join(Machine)
        q = q.join(Interface)
        q = q.options(contains_eager('machine'),
                      contains_eager('machine.interfaces'))
        # TODO: add eager-loading options
        q = q.reset_joinpoint()

        dbarchetype = None
        feature_type = None

        # Warning: order matters here!
        params = {}
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                        compel=True)

            if dbmodel.machine_type == "nic":
                feature_type = "interface"
            else:
                feature_type = "hardware"

            params["model"] = dbmodel

            # The default for models...
            justification_required = True

            if personality:
                # ... except if restricted to a single personality
                justification_required = False
                dbpersonality = Personality.get_unique(session,
                                                       name=personality,
                                                       archetype=archetype,
                                                       compel=True)
                params["personality"] = dbpersonality
                if interface:
                    params["interface_name"] = interface
                    q = q.filter(Interface.name == interface)
                dbarchetype = dbpersonality.archetype
                q = q.filter_by(personality=dbpersonality)
            elif archetype:
                dbarchetype = Archetype.get_unique(session, archetype,
                                                   compel=True)
                params["archetype"] = dbarchetype
                q = q.join(Personality)
                q = q.options(contains_eager("personality"))
                q = q.filter_by(archetype=dbarchetype)
            else:
                # It's highly unlikely that a feature template would work for
                # _any_ archetype, so disallow this case for now. As I can't
                # rule out that such a case will not have some uses in the
                # future, the restriction is here and not in the model.
                raise ArgumentError("Please specify either an archetype or "
                                    "a personality when binding a feature to "
                                    "a model.")

            q = q.filter(or_(Machine.model == dbmodel,
                             Interface.model == dbmodel))
        elif personality:
            if interface:
                feature_type = "interface"
                params["interface_name"] = interface
                q = q.filter(Interface.name == interface)
            else:
                feature_type = "host"
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            params["personality"] = dbpersonality
            dbarchetype = dbpersonality.archetype
            q = q.filter_by(personality=dbpersonality)
        elif archetype:
            justification_required = True

            feature_type = "host"
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            params["archetype"] = dbarchetype
            q = q.join(Personality)
            q = q.options(contains_eager("personality"))
            q = q.filter_by(archetype=dbarchetype)

        if dbarchetype and not dbarchetype.is_compileable:
            raise UnimplementedError("Binding features to non-compilable "
                                     "archetypes is not implemented.")

        if not feature_type:  # pragma: no cover
            raise InternalError("Feature type is not known.")

        dbfeature = Feature.get_unique(session, name=feature,
                                       feature_type=feature_type, compel=True)

        self.do_link(session, logger, dbfeature, params)
        session.flush()

        # Note: due to the joins it is the number of interfaces (incl.
        # management), not the number of hosts
        cnt = q.count()

        # TODO: should the limit be configurable?
        if justification_required and cnt > 0:
            if not justification:
                raise AuthorizationException("Changing feature bindings for more "
                                             "than just a personality "
                                             "requires --justification.")
            validate_justification(user, justification)

        if not flush:
            return

        idx = 0
        written = 0
        successful = []
        failed = []

        with CompileKey(logger=logger) as key:
            hosts = q.all()

            logger.client_info("Flushing %d hosts." % len(hosts))

            for host in q.all():
                idx += 1
                if idx % 1000 == 0:  # pragma: no cover
                    logger.client_info("Processing host %d of %d..." %
                                       (idx, cnt))

                if not host.archetype.is_compileable:  # pragma: no cover
                    continue

                try:
                    plenary_host = PlenaryHost(host)
                    written += plenary_host.write(locked=True)
                    successful.append(plenary_host)
                except IncompleteError:
                    pass
                except Exception, err:  # pragma: no cover
                    failed.append("{0} failed: {1}".format(host, err))

            if failed:  # pragma: no cover
                for plenary in successful:
                    plenary.restore_stash()
                raise PartialError([], failed)

            # FIXME: we should also try to compile, but we don't have a good
            # interface for compiling a bunch of hosts in an unknown number of
            # domains/sandboxes.

        logger.client_info("Flushed %d/%d templates." %
                           (written, written + len(failed)))

        return

    def do_link(self, session, logger, dbfeature, params):
        FeatureLink.get_unique(session, feature=dbfeature, preclude=True,
                               **params)

        # Binding a feature both at the personality and at the archetype level
        # is not an error, as the templete generation will skip duplicates.
        # Still it is worth to emit a warning so the user is aware of this case.
        q = session.query(FeatureLink)
        q = q.filter_by(feature=dbfeature,
                        model=params.get("model", None))
        if "personality" in params and "interface_name" not in params:
            q = q.filter_by(archetype=params["personality"].archetype,
                            personality=None)
            if q.first():
                logger.client_info("Warning: {0:l} is already bound to {1:l}; "
                                   "binding it to {2:l} is redundant."
                                   .format(dbfeature,
                                           params["personality"].archetype,
                                           params["personality"]))
        elif "archetype" in params:
            q = q.filter_by(interface_name=None)
            q = q.join(Personality)
            q = q.filter_by(archetype=params["archetype"])
            for link in q.all():
                logger.client_info("Warning: {0:l} is bound to {1:l} which "
                                   "is now redundant; consider removing it."
                                   .format(dbfeature, link.personality))

        dbfeature.links.append(FeatureLink(**params))
