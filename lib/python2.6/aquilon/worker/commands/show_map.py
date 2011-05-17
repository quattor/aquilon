# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq show map`."""


from aquilon.exceptions_ import UnimplementedError, NotFoundException
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (Personality, Service, ServiceMap,
                                PersonalityServiceMap)
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.service_map import ServiceMapList


class CommandShowMap(BrokerCommand):

    required_parameters = []

    def render(self, session, service, instance, archetype, personality,
               **arguments):
        dbservice = service and Service.get_unique(session, service,
                                                   compel=True) or None
        dblocation = get_location(session, **arguments)
        queries = []
        # The current logic basically shoots for exact match when given
        # (like exact personality maps only or exact archetype maps
        # only), or "any" if an exact spec isn't given.
        if archetype and personality:
            dbpersona = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
            q = session.query(PersonalityServiceMap)
            q = q.filter_by(personality=dbpersona)
            queries.append(q)
        elif personality:
            # Alternately, this could throw an error and ask for archetype.
            q = session.query(PersonalityServiceMap)
            q = q.join('personality').filter_by(name=personality)
            q = q.reset_joinpoint()
            queries.append(q)
        elif archetype:
            # Alternately, this could throw an error and ask for personality.
            q = session.query(PersonalityServiceMap)
            q = q.join(['personality', 'archetype']).filter_by(name=archetype)
            q = q.reset_joinpoint()
            queries.append(q)
        else:
            queries.append(session.query(ServiceMap))
            queries.append(session.query(PersonalityServiceMap))
        if dbservice:
            for i in range(len(queries)):
                queries[i] = queries[i].join('service_instance')
                queries[i] = queries[i].filter_by(service=dbservice)
                queries[i] = queries[i].reset_joinpoint()
        if instance:
            for i in range(len(queries)):
                queries[i] = queries[i].join('service_instance')
                queries[i] = queries[i].filter_by(name=instance)
                queries[i] = queries[i].reset_joinpoint()
        # Nothing fancy for now - just show any relevant explicit bindings.
        if dblocation:
            for i in range(len(queries)):
                queries[i] = queries[i].filter_by(location=dblocation)
        results = ServiceMapList()
        for q in queries:
            results.extend(q.all())
        if service and instance and dblocation:
            # This should be an exact match.  (Personality doesn't
            # matter... either it was given and it should be an
            # exact match for PersonalityServiceMap or it wasn't
            # and this should be an exact match for ServiceMap.)
            if not results:
                raise NotFoundException("No matching map found.")
        return results
