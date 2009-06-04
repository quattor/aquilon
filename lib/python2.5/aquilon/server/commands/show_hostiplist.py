# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Contains the logic for `aq show hostiplist`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.host import HostIPList
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.model import System


class CommandShowHostIPList(BrokerCommand):

    default_style = "csv"

    def render(self, session, **arguments):
        # FIXME: Currently ignores archetype and outputs regardless
        # of whether we want hosts...
        #archetype = arguments.get("archetype", None)
        #if archetype:
        #    dbarchetype = get_archetype(session, archetype)
        iplist = HostIPList()
        q = session.query(System)
        # Outer-join in all the subclasses so that each access of
        # system doesn't (necessarily) issue another query.
        q = q.with_polymorphic(System.__mapper__.polymorphic_map.values())
        # Right now, this is returning everything with an ip.
        q = q.filter(System.ip!=None)
        for system in q.all():
            # Do not include aurora hosts.  We are not canonical for
            # this information.  At least, not yet.
            if (system.system_type == 'host' and
                    system.archetype.name == 'aurora'):
                continue
            entry = [system.fqdn, system.ip]
            # For names on alternate interfaces, also provide the
            # name for the bootable (primary) interface.  This allows
            # the reverse IP address to be set to the primary.
            # This is inefficient, but OK for now since we only have
            # a few auxiliary systems.
            if system.system_type == 'auxiliary' and system.machine.host:
                entry.append(system.machine.host.fqdn)
            else:
                entry.append("")
            iplist.append(entry)
        return iplist
