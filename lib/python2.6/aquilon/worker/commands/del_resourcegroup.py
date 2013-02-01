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


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ResourceGroup, ServiceAddress
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)


class CommandDelResourceGroup(BrokerCommand):

    required_parameters = ["resourcegroup"]

    def render(self, session, logger, resourcegroup, hostname, cluster,
               **arguments):

        validate_basic("resourcegroup", resourcegroup)
        holder = get_resource_holder(session, hostname, cluster, compel=True)
        dbrg = ResourceGroup.get_unique(session, name=resourcegroup,
                                        holder=holder, compel=True)

        # Deleting service addresses can't be done with just cascading
        if dbrg.resholder:
            for res in dbrg.resholder.resources:
                if isinstance(res, ServiceAddress):
                    raise ArgumentError("{0} contains {1:l}, please delete "
                                        "it first.".format(dbrg, res))

        del_resource(session, logger, dbrg)
        return
