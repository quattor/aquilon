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


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import (ServiceAddress, ResourceGroup,
                                AddressAssignment, Host)
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.resources import (del_resource,
                                                 get_resource_holder)
from aquilon.worker.processes import DSDBRunner

def del_srv_dsdb_callback(session, logger, holder, dbsrv_addr, oldinfo,
                          keep_dns):
    real_holder = holder.holder_object
    if isinstance(real_holder, ResourceGroup):
        real_holder = real_holder.holder.holder_object

    dsdb_runner = DSDBRunner(logger=logger)
    try:
        if isinstance(real_holder, Host):
            dsdb_runner.update_host(real_holder.machine, oldinfo)
            if keep_dns:
                dsdb_runner.add_host_details(fqdn=dbsrv_addr.dns_record.fqdn,
                                             ip=dbsrv_addr.dns_record.ip,
                                             name=None, mac=None,
                                             comments=dbsrv_addr.dns_record.comments)
        elif not keep_dns:
            dsdb_runner.delete_host_details(dbsrv_addr.dns_record.ip)
    except ProcessException, e:
        raise ArgumentError("Could not delete host from DSDB: %s" % e)


class CommandDelServiceAddress(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, logger, name, hostname, cluster, resourcegroup,
               keep_dns, **arguments):

        validate_basic("name", name)

        if name == "hostname":
            raise ArgumentError("The primary address of the host cannot "
                                "be deleted.")

        holder = get_resource_holder(session, hostname, cluster,
                                     resourcegroup, compel=False)

        dbsrv = ServiceAddress.get_unique(session, name=name, holder=holder,
                                          compel=True)

        if isinstance(holder.holder_object, Host):
            oldinfo = DSDBRunner.snapshot_hw(holder.holder_object.machine)
        else:
            oldinfo = None

        dbdns_rec = dbsrv.dns_record

        for addr in dbsrv.assignments:
            addr.interface.assignments.remove(addr)
        session.expire(dbsrv, ['assignments'])

        session.flush()

        # Check if the address was assigned to multiple interfaces, and remove
        # the DNS entries if this was the last use
        q = session.query(AddressAssignment)
        q = q.filter_by(network=dbdns_rec.network)
        q = q.filter_by(ip=dbdns_rec.ip)
        other_uses = q.all()

        del_resource(session, logger, dbsrv,
                     dsdb_callback=del_srv_dsdb_callback, oldinfo=oldinfo,
                     keep_dns=other_uses or keep_dns)

        if not other_uses and not keep_dns:
            delete_dns_record(dbdns_rec)

        return
