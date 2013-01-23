# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq add personality`."""


import re

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (Archetype, Personality,
                                Parameter, HostEnvironment,
                                PersonalityParameter)
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.templates.personality import PlenaryPersonality
from aquilon.worker.dbwrappers.parameter import get_parameters
from aquilon.worker.dbwrappers.feature import add_link
from aquilon.worker.dbwrappers.grn import lookup_grn


class CommandAddPersonality(BrokerCommand):

    required_parameters = ["personality", "archetype", "host_environment"]

    def render(self, session, logger, personality, archetype, grn, eon_id, host_environment,
               comments, cluster_required, copy_from, config_override, **arguments):

        valid = re.compile('^[a-zA-Z0-9_-]+\/?[a-zA-Z0-9_-]+$')
        if not valid.match(personality):
            raise ArgumentError("Personality name '%s' is not valid." %
                                personality)
        if not (grn or eon_id):
            raise ArgumentError("GRN or EON ID is required for adding a "
                                "personality.")

        HostEnvironment.validate_name(host_environment)
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        Personality.get_unique(session, archetype=dbarchetype,
                               name=personality,
                               preclude=True)

        host_env = HostEnvironment.get_unique(session, host_environment, compel=True)
        dbpersona = Personality(name=personality, archetype=dbarchetype,
                                cluster_required=bool(cluster_required),
                                config_override=config_override,
                                host_environment=host_env,
                                comments=comments)

        ##configuration override
        session.add(dbpersona)

        ## add grn/eonid
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)
        dbpersona.grns.append(dbgrn)

        if copy_from:
            ## copy config data
            dbfrom_persona = Personality.get_unique(session,
                                                    archetype=dbarchetype,
                                                    name=copy_from,
                                                    compel=True)

            src_parameters = get_parameters(session,
                                            personality=dbfrom_persona)
            db_param_holder = PersonalityParameter(personality=dbpersona)

            for param in src_parameters:
                dbparameter = Parameter(value=param.value,
                                        comments=param.comments,
                                        holder=db_param_holder)
                session.add(dbparameter)

            for link in dbfrom_persona.features:
                params = {}
                params["personality"] = dbpersona
                if link.model:
                    params["model"] = link.model
                if link.interface_name:
                    params["interface_name"] = link.interface_name

                add_link(session, logger, link.feature, params)

        session.flush()

        plenary = PlenaryPersonality(dbpersona, logger=logger)
        plenary.write()
        return
