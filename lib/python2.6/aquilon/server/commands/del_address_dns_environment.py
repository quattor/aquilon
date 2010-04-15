# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import FutureARecord
from aquilon.exceptions_ import UnimplementedError, ArgumentError
from aquilon.server.locks import lock_queue, DeleteKey
from aquilon.server.processes import DSDBRunner
from aquilon.server.dbwrappers.system import (get_system,
                                              get_system_dependencies)


class CommandDelAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["fqdn", "ip", "dns_environment"]

    def render(self, session, logger, fqdn, ip, dns_environment, **arguments):
        default = self.config.get("broker", "default_dns_environment")
        if str(dns_environment).strip().lower() != default.strip().lower():
            raise UnimplementedError("Only the '%s' DNS environment is "
                                     "currently supported." % default)

        key = DeleteKey("system", logger=logger)
        try:
            lock_queue.acquire(key)
            dbaddress = get_system(session, fqdn, FutureARecord, 'DNS Record')
            if ip != dbaddress.ip:
                raise ArgumentError("IP address %s is not set for %s (%s).",
                                    (ip, dbaddress.fqdn, dbaddress.ip))
            if dbaddress.hardware_entity:
                raise ArgumentError("DNS record {0:a} is the primary name of "
                                    "{1:l}, therefore it cannot be "
                                    "deleted.".format(dbaddress,
                                                      dbaddress.hardware_entity))
            deps = get_system_dependencies(session, dbaddress)
            if deps:
                raise ArgumentError("Cannot remove address for %s (%s) while "
                                    "the following dependencies exist:\n%s" %
                                    (dbaddress.fqdn, dbaddress.ip,
                                     "\n".join(deps)))
            session.delete(dbaddress)
            session.flush()

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.delete_host_details(ip)
            session.commit()
        finally:
            lock_queue.release(key)
        return
