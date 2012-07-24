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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Personality, Archetype
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import (get_parameter_holder,
                                                 set_parameter)
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddParameter(BrokerCommand):

    required_parameters = ['path']

    def process_parameter(self, session, param_holder, path, value, comments):

        dbparameter = set_parameter(session, param_holder, path, value,
                                    compel=False, preclude=True)
        if comments:
            dbparameter.comments = comments

        return dbparameter

    def render(self, session, logger, archetype, personality, feature,
               path, value=None, comments=None, **arguments):

        if not personality:
            if not feature:
                raise ArgumentError("Parameters can be added for personality "
                                    "or feature.")
            if not archetype:
                raise ArgumentError("Adding parameter on feature binding "
                                    "needs personality or archetype")

        param_holder = get_parameter_holder(session, archetype, personality,
                                            feature, auto_include=True)

        if isinstance(param_holder.holder_object, Personality) and \
           not param_holder.holder_object.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(param_holder.holder_object.archetype))

        dbparameter = self.process_parameter(session, param_holder, path, value,
                                             comments)
        session.add(dbparameter)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)

        if feature:
            q = session.query(Personality)
            if personality:
                q = q.filter_by(name=personality)
            elif archetype:
                dbarchetype = Archetype.get_unique(session, archetype,
                                                   compel=True)
                q = q.filter_by(archetype=dbarchetype)
            for dbpers in q:
                plenaries.append(Plenary.get_plenary(dbpers))
        else:
            plenaries.append(Plenary.get_plenary(param_holder.holder_object))

        plenaries.write()
