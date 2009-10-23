# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Contains the logic for `aq update machine`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import (ArgumentError, NotFoundException)
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.aqdb.model import Network
import re

class CommandUpdateNetwork(BrokerCommand):

    def render(self, session, network, discovered, discoverable, ip, user, type=False, **arguments):

        required_parameters = []
        networks = []

        if network or ip:
            dbnetwork = network and get_network_byname(session, network) or None
            dbnetwork = ip and get_network_byip(session, ip) or dbnetwork
            if not dbnetwork:
                raise NotFoundException('No valid network supplied')
            networks.append(dbnetwork)
        else:
            q = session.query(Network)
            if type:
                q = q.filter_by(network_type = type)
            dblocation = get_location(session, **arguments)
            if dblocation:
                q = q.filter_by(location=dblocation)
            networks.extend(q.all())
            if len(networks) <= 0:
                raise NotFoundException('No existing networks with the specified network type or location')

        yes = re.compile("^(true|yes|y|1|on|enabled)$", re.I)
        no = re.compile("^(false|no|n|0|off|disabled)$", re.I)
        if discovered:
            if yes.match(discovered):
                discovered = "y"
            elif no.match(discovered):
                discovered = "n"
            else:
                raise ArgumentError('Did not recognise supplied argument to discovered flag: "%s"' % discovered)
        if discoverable:
            if yes.match(discoverable):
                discoverable = "y"
            elif no.match(discoverable):
                discoverable = "n"
            else:
                raise ArgumentError('Did not recognise supplied argument to discoverable flag: "%s"' % discoverable)

        for net in networks:
            if discoverable:
                if discoverable == "y":
                    net.is_discoverable = True
                elif discoverable == "n":
                    net.is_discoverable = False
            if discovered:
                if discovered == "y":
                    net.is_discovered = True
                elif discovered == "n":
                    net.is_discovered = False
