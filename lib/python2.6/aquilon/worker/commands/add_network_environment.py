# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add network_environment`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.aqdb.model import NetworkEnvironment, DnsEnvironment
from aquilon.worker.dbwrappers.location import get_location


class CommandAddNetworkEnvironment(BrokerCommand):

    required_parameters = ["network_environment"]

    def render(self, session, network_environment, dns_environment, comments,
               **arguments):
        validate_basic("network environment", network_environment)
        NetworkEnvironment.get_unique(session, network_environment,
                                      preclude=True)
        dbdns_env = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)

        # Currently input.xml lists --building only, but that may change
        location = get_location(session, **arguments)

        dbnet_env = NetworkEnvironment(name=network_environment,
                                       dns_environment=dbdns_env,
                                       location=location, comments=comments)

        if dbdns_env.is_default != dbnet_env.is_default:
            raise ArgumentError("Only the default network environment may be "
                                "associated with the default DNS environment.")

        session.add(dbnet_env)
        session.flush()
        return
