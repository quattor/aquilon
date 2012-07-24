# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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


from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import ParamDefinition
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers.parameter import (validate_value,
                               get_param_def_holder)


class CommandAddParameterDefintion(BrokerCommand):

    required_parameters = ["path", "value_type"]

    def render(self, session, archetype, feature, feature_type, template, path,
               value_type, required, default, description, **kwargs):

        if archetype:
            if not template:
                raise ArgumentError("Template must be specified for archetype "
                                    "parameter definition.")
        elif not feature:
            raise ArgumentError("Archetype or Feature must be specified for "
                                "parameter definition.")

        ParamDefinition.validate_type(value_type)

        if default:
            validate_value("default for path=%s" % path, value_type, default)

        db_paramdef_holder = get_param_def_holder(session, archetype,
                                                  feature, feature_type,
                                                  auto_include=True)

        if archetype and not db_paramdef_holder.holder_object.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(db_paramdef_holder.holder_object))

        ParamDefinition.get_unique(session, path=path,
                                   holder=db_paramdef_holder, preclude=True)

        db_paramdef = ParamDefinition(path=path, holder=db_paramdef_holder,
                                      value_type=value_type, default=default,
                                      required=required, template=template,
                                      description=description)
        session.add(db_paramdef)
        session.flush()

        return
