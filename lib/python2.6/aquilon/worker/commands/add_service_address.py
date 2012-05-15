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


from aquilon.exceptions_ import (ArgumentError, UnimplementedError,
                                 ProcessException)
from aquilon.aqdb.model import ServiceAddress, Cluster, Host, ResourceGroup
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.interface import assign_address
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)
from aquilon.worker.processes import DSDBRunner


def add_srv_dsdb_callback(session, logger, dbsrv, real_holder=None,
                          oldinfo=None, newly_created=None, comments=None):
    try:
        dsdb_runner = DSDBRunner(logger=logger)
        # FIXME: this is not rolled back if the following operations fail
        if not newly_created:
            dsdb_runner.delete_host_details(dbsrv.dns_record.ip)
        if isinstance(real_holder, Host):
            dsdb_runner.update_host(real_holder.machine, oldinfo)
        else:
            dsdb_runner.add_host_details(str(dbsrv.dns_record.fqdn),
                                         dbsrv.dns_record.ip, None, None,
                                         comments=comments)
    except ProcessException, e:
        raise ArgumentError("Could not add host to DSDB: %s" % e)


class CommandAddServiceAddress(BrokerCommand):

    required_parameters = ["service_address", "name", "interfaces"]

    def render(self, session, logger, service_address, ip, name, interfaces,
               hostname, cluster, resourcegroup,
               network_environment, comments, **arguments):

        validate_basic("name", name)

        # TODO: generalize the error message - Layer-3 failover may be
        # implemented by other software, not just Zebra.
        if name == "hostname":
            raise ArgumentError("The hostname service address is reserved for "
                                "Zebra.  Please specify the --zebra_interfaces "
                                "option when calling add_host if you want the "
                                "primary name of the host to be managed by "
                                "Zebra.")

        ifnames = [ifname.strip().lower() for ifname in interfaces.split(",")]
        if not ifnames:
            raise ArgumentError("Please specify at least one interface name.")

        holder = get_resource_holder(session, hostname, cluster,
                                     resourcegroup, compel=False)

        # Address assignments should be added based on the host/cluster, so we
        # have to resolve resource groups first
        if isinstance(holder.holder_object, ResourceGroup):
            real_holder = holder.holder_object.holder.holder_object
        else:
            real_holder = holder.holder_object

        ServiceAddress.get_unique(session, name=name, holder=holder,
                                  preclude=True)

        dbdns_rec, newly_created = grab_address(session, service_address, ip,
                                                network_environment,
                                                allow_multi=True)
        ip = dbdns_rec.ip
        dbnetwork = dbdns_rec.network

        # Disable autoflush, since the ServiceAddress object won't be complete
        # until add_resource() is called
        # TODO: In SQLA 0.7.6, we'd be able to use "with session.no_autoflush:"
        saved_autoflush = session.autoflush
        session.autoflush = False

        dbsrv = ServiceAddress(name=name, dns_record=dbdns_rec,
                               comments=comments)
        holder.resources.append(dbsrv)

        oldinfo = None
        if isinstance(real_holder, Cluster):
            if not real_holder.hosts:
                # The interface names are only stored in the AddressAssignment
                # objects, so we can't handle a cluster with no hosts and thus
                # no interfaces
                raise ArgumentError("Cannot assign a service address to a "
                                    "cluster that has no members.")
            for host in real_holder.hosts:
                apply_service_address(host, ifnames, dbsrv)
        elif isinstance(real_holder, Host):
            oldinfo = DSDBRunner.snapshot_hw(real_holder.machine)
            apply_service_address(real_holder, ifnames, dbsrv)
        else:  # pragma: no cover
            raise UnimplementedError("{0} as a resource holder is not "
                                     "implemented.".format(real_holder))

        session.autoflush = saved_autoflush

        add_resource(session, logger, holder, dbsrv,
                     dsdb_callback=add_srv_dsdb_callback,
                     real_holder=real_holder, oldinfo=oldinfo,
                     newly_created=newly_created, comments=comments)

        return

def apply_service_address(dbhost, ifnames, srv_addr):
    for ifname in ifnames:
        dbinterface = None
        for iface in dbhost.machine.interfaces:
            if iface.name == ifname:
                dbinterface = iface
                break
        if not dbinterface:
            raise ArgumentError("{0} does not have an interface named "
                                "{1}.".format(dbhost.machine, ifname))

        assign_address(dbinterface, srv_addr.dns_record.ip,
                       srv_addr.dns_record.network, label=srv_addr.name,
                       resource=srv_addr)
