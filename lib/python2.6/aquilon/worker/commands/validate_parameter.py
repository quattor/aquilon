# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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


from aquilon.worker.formats.parameter_definition import ParamDefinitionFormatter
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import FeatureLinkParameter, PersonalityParameter
from aquilon.worker.dbwrappers.parameter import (get_parameter_holder,
                                                 get_parameters)
from aquilon.exceptions_ import ArgumentError


class CommandValidateParameter(BrokerCommand):

    def render(self, session, logger, personality, archetype, feature,
               **arguments):

        if not personality:
            if not feature:
                raise ArgumentError("Parameters can be validated for "
                                    "personality or feature.")
            if not archetype:
                raise ArgumentError("Validating parameter on feature binding "
                                    "needs personality or archetype.")

        param_holder = get_parameter_holder(session, archetype, personality,
                                            feature)

        if isinstance(param_holder, FeatureLinkParameter):
            paramdef_holder = param_holder.featurelink.feature.paramdef_holder
            parameters = get_parameters(session,
                                        featurelink=param_holder.featurelink)
        elif isinstance(param_holder, PersonalityParameter):
            paramdef_holder = param_holder.personality.archetype.paramdef_holder
            parameters = get_parameters(session,
                                        personality=param_holder.personality)
        else:
            paramdef_holder = None
            parameters = []

        if paramdef_holder:
            param_definitions = paramdef_holder.param_definitions
        else:
            param_definitions = []

        errors = []
        formatter = ParamDefinitionFormatter()

        for param_def in param_definitions:
            ## ignore not required fields or fields
            ## which have defaults specified
            if (not param_def.required) or param_def.default:
                continue

            value = None
            for param in parameters:
                value = param.get_path(param_def.path, compel=False)
                if value:
                    break

            ## ignore if value is specified
            if value is None:
                errors.append(formatter.format_raw(param_def))

        if errors:
            raise ArgumentError("Following required parameters have not been "
                                "specified:\n" +
                                "\n".join([error for error in errors]))

        logger.client_info("All required parameters specified.")
        return
