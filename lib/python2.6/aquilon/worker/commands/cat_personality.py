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
"""Contains the logic for `aq cat --personality`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Personality
from aquilon.worker.templates.personality import (PlenaryPersonality,
                                                  PlenaryPersonalityPreFeature,
                                                  PlenaryPersonalityPostFeature,
                                                  PlenaryPersonalityParameter,
                                                  PlenaryPersonalityBase)
from aquilon.exceptions_ import NotFoundException


class CommandCatPersonality(BrokerCommand):

    required_parameters = ["personality"]

    def render(self, generate, session, logger, personality, archetype,
               pre_feature, post_feature, param_tmpl, **kwargs):
        dbpersonality = Personality.get_unique(session, archetype=archetype,
                                               name=personality, compel=True)

        plenary = PlenaryPersonalityBase(dbpersonality, logger=logger)
        if pre_feature:
            plenary = PlenaryPersonalityPreFeature(dbpersonality, logger=logger)

        if post_feature:
            plenary = PlenaryPersonalityPostFeature(dbpersonality, logger=logger)

        if param_tmpl:
            param_templates = PlenaryPersonality.get_parameters_by_tmpl(dbpersonality)
            if param_tmpl in param_templates.keys():
                plenary = PlenaryPersonalityParameter(param_tmpl, param_templates[param_tmpl],
                                                      dbpersonality, logger=logger)
            else:
                raise NotFoundException("No parameter template %s.tpl found." %
                                        param_tmpl)

        lines = []
        if generate:
            lines.append(plenary._generate_content())
        else:
            lines.append(plenary.read())

        return lines
