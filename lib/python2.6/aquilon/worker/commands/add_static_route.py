# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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
"""Contains the logic for `aq add static route`."""

from ipaddr import IPv4Network

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import NetworkEnvironment, StaticRoute
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddStaticRoute(BrokerCommand):

    required_parameters = ["gateway", "ip"]

    def render(self, session, gateway, ip, netmask, prefixlen,
               network_environment, comments, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = get_net_id_from_ip(session, gateway, dbnet_env)

        if netmask:
            dest = IPv4Network("%s/%s" % (ip, netmask))
        else:
            dest = IPv4Network("%s/%s" % (ip, prefixlen))

        # TODO: this will have to be changed if we want equal cost multipath
        # etc.
        for route in dbnetwork.static_routes:
            if dest.overlaps(route.destination):
                raise ArgumentError("{0} already has an overlapping route to "
                                    "{1} using gateway {2}."
                                    .format(dbnetwork, route.destination,
                                            route.gateway_ip))

        route = StaticRoute(network=dbnetwork, dest_ip=dest.ip,
                            dest_cidr=dest.prefixlen, gateway_ip=gateway,
                            comments=comments)
        session.add(route)
        session.flush()

        # TODO: refresh affected host templates
        return
