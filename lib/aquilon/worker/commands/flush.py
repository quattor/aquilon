# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq flush`."""


from collections import defaultdict
from operator import attrgetter

from sqlalchemy.orm import joinedload, subqueryload, lazyload, contains_eager
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import PartialError, IncompleteError
from aquilon.aqdb.model import (Service, Machine, Chassis, Host,
                                Personality, Cluster, City, Rack, Resource,
                                ResourceHolder, HostResource, ClusterResource,
                                VirtualMachine, Filesystem, RebootSchedule,
                                Share, Disk, Interface, AddressAssignment,
                                ServiceInstance, Switch)
from aquilon.aqdb.data_sync.storage import cache_storage_data
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.base import Plenary
from aquilon.worker.locks import CompileKey


class CommandFlush(BrokerCommand):

    def render(self, session, logger,
               services, personalities, machines, clusters, hosts,
               locations, resources, switches, all,
               **arguments):
        success = []
        failed = []
        written = 0

        # Caches for keeping preloaded data pinned in memory, since the SQLA
        # session holds a weak reference only
        resource_by_id = {}
        resholder_by_id = {}
        service_instances = None
        racks = None

        # Object caches that are accessed directly
        disks_by_machine = defaultdict(list)
        interfaces_by_machine = defaultdict(list)
        interfaces_by_id = {}

        if all:
            services = True
            personalities = True
            machines = True
            clusters = True
            hosts = True
            locations = True
            resources = True

        with CompileKey(logger=logger):
            logger.client_info("Loading data.")

            # When flushing clusters/hosts, loading the resource holder is done
            # as the query that loads those objects. But when flushing resources
            # only, we need the holder and the object it belongs to.
            if resources and not clusters:
                q = session.query(ClusterResource)
                # Using joinedload('cluster') would generate an outer join
                q = q.join(Cluster)
                q = q.options(contains_eager('cluster'))
                for resholder in q:
                    resholder_by_id[resholder.id] = resholder
            if resources and not hosts:
                q = session.query(HostResource)
                # Using joinedload('host') would generate an outer join
                q = q.join(Host)
                q = q.options(contains_eager('host'))
                for resholder in q:
                    resholder_by_id[resholder.id] = resholder

            if hosts or clusters or resources:
                # Load the most common resource types. Using
                # with_polymorphic('*') on Resource would generate a huge query,
                # so do something more targeted. More resource subclasses may be
                # added later if they become common.
                preload_classes = {
                    Filesystem: [],
                    RebootSchedule: [],
                    VirtualMachine: [joinedload('machine'),
                                     joinedload('machine.primary_name'),
                                     joinedload('machine.primary_name.fqdn')],
                    Share: [],
                }

                share_info = cache_storage_data()

                for cls, options in preload_classes.items():
                    q = session.query(cls)

                    # If only hosts or only clusters are needed, don't load
                    # resources of the other kind
                    if hosts and not clusters and not resources:
                        q = q.join(ResourceHolder)
                        q = q.options(contains_eager('holder'))
                        q = q.filter_by(holder_type='host')
                    if clusters and not hosts and not resources:
                        q = q.join(ResourceHolder)
                        q = q.filter_by(holder_type='cluster')
                        q = q.options(contains_eager('holder'))

                    if options:
                        q = q.options(*options)

                    for res in q:
                        resource_by_id[res.id] = res
                        try:
                            res.populate_share_info(share_info)
                        except AttributeError:
                            pass

            if hosts or machines:
                # Polymorphic loading cannot be applied to eager-loaded
                # attributes, so load interfaces manually.
                q = session.query(Interface)
                q = q.with_polymorphic('*')
                q = q.options(lazyload("hardware_entity"))
                for iface in q:
                    interfaces_by_machine[iface.hardware_entity_id].append(iface)
                    interfaces_by_id[iface.id] = iface

                if hosts:
                    # subqueryload() and with_polymorphic() do not play nice
                    # together, so do it by hand
                    q = session.query(AddressAssignment)
                    q = q.options(joinedload("network"),
                                  joinedload("dns_records"))
                    q = q.order_by(AddressAssignment._label)
                    addrs_by_iface = defaultdict(list)
                    for addr in q:
                        addrs_by_iface[addr.interface_id].append(addr)
                    for interface_id, addrs in addrs_by_iface.items():
                        set_committed_value(interfaces_by_id[interface_id],
                                            "assignments", addrs)

                    q = session.query(Interface.id)
                    q = q.filter(~Interface.assignments.any())
                    for id in q.all():
                        set_committed_value(interfaces_by_id[id[0]],
                                            "assignments", None)

            if hosts or services:
                q = session.query(ServiceInstance)
                q = q.options(subqueryload("service"))
                service_instances = q.all()

            if machines or clusters:
                # Most machines are in racks...
                q = session.query(Rack)
                q = q.options(subqueryload("dns_maps"),
                              subqueryload("parents"))
                racks = q.all()

            if locations:
                logger.client_info("Flushing locations.")
                for dbloc in session.query(City).all():
                    try:
                        plenary = Plenary.get_plenary(dbloc, logger=logger)
                        written += plenary.write(locked=True)
                    except Exception, e:
                        failed.append("City %s failed: %s" %
                                      dbloc, e)
                        continue

            if services:
                logger.client_info("Flushing services.")
                q = session.query(Service)
                q = q.options(subqueryload("instances"))
                for dbservice in q:
                    try:
                        plenary_info = Plenary.get_plenary(dbservice,
                                                           logger=logger)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        failed.append("Service %s failed: %s" %
                                      (dbservice.name, e))
                        continue

                    for dbinst in dbservice.instances:
                        try:
                            plenary_info = Plenary.get_plenary(dbinst,
                                                               logger=logger)
                            written += plenary_info.write(locked=True)
                        except Exception, e:
                            failed.append("Service %s instance %s failed: %s" %
                                          (dbservice.name, dbinst.name, e))
                            continue

            if personalities:
                logger.client_info("Flushing personalities.")
                for persona in session.query(Personality).all():
                    try:
                        plenary_info = Plenary.get_plenary(persona,
                                                           logger=logger)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        failed.append("Personality %s failed: %s" %
                                      (persona.name, e))
                        continue

            if machines:
                logger.client_info("Flushing machines.")

                # Polymorphic loading cannot be applied to eager-loaded
                # attributes, so load disks manually
                q = session.query(Disk)
                q = q.with_polymorphic('*')
                for disk in q:
                    disks_by_machine[disk.machine_id].append(disk)

                # Load chassis
                q = session.query(Chassis)
                q = q.options(joinedload("primary_name"),
                              joinedload("primary_name.fqdn"))
                chassis = q.all()

                # Load manager addresses
                # TODO: only if not hosts
                manager_addrs = defaultdict(list)
                q = session.query(AddressAssignment)
                q = q.join(Interface)
                q = q.filter_by(interface_type="management")
                q = q.options(contains_eager("interface"),
                              joinedload("dns_records"),
                              lazyload("interface.hardware_entity"))
                for addr in q:
                    manager_addrs[addr.interface.id].append(addr)
                for interface_id, addrs in manager_addrs.items():
                    if interface_id not in interfaces_by_id:
                        # Should not happen...
                        continue
                    addrs.sort(key=attrgetter("label"))
                    set_committed_value(interfaces_by_id[interface_id],
                                        "assignments", addrs)

                q = session.query(Machine)
                q = q.options(lazyload("host"),
                              lazyload("primary_name"),
                              subqueryload("chassis_slot"))

                cnt = q.count()
                idx = 0
                for machine in q:
                    idx += 1
                    if idx % 1000 == 0:  # pragma: no cover
                        logger.client_info("Processing machine %d of %d..." %
                                           (idx, cnt))

                    if machine.id in disks_by_machine:
                        disks_by_machine[machine.id].sort(key=attrgetter('device_name'))
                        set_committed_value(machine, 'disks',
                                            disks_by_machine[machine.id])

                    if machine.id in interfaces_by_machine:
                        interfaces_by_machine[machine.id].sort(key=attrgetter('name'))
                        set_committed_value(machine, 'interfaces',
                                            interfaces_by_machine[machine.id])

                    try:
                        plenary_info = Plenary.get_plenary(machine,
                                                           logger=logger)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        label = machine.label
                        if machine.host:
                            label = "%s (host: %s)" % (machine.label,
                                                       machine.host.fqdn)
                        failed.append("Machine %s failed: %s" % (label, e))
                        continue

            if hosts:
                logger.client_info("Flushing hosts.")

                q = session.query(Cluster)
                q = q.options(subqueryload("_metacluster"),
                              joinedload("_metacluster.metacluster"),
                              lazyload("location_constraint"),
                              lazyload("personality"),
                              lazyload("branch"))
                cluster_cache = q.all()

                cnt = session.query(Host).count()
                idx = 0
                q = session.query(Host)
                q = q.options(joinedload("machine"),
                              joinedload("machine.primary_name"),
                              joinedload("machine.primary_name.fqdn"),
                              subqueryload("_grns"),
                              subqueryload("resholder"),
                              subqueryload("services_used"),
                              subqueryload("_services_provided"),
                              subqueryload("_cluster"),
                              lazyload("_cluster.host"),
                              lazyload("_cluster.cluster"))
                for h in q:
                    idx += 1
                    if idx % 1000 == 0:  # pragma: no cover
                        logger.client_info("Processing host %d of %d..." %
                                           (idx, cnt))

                    if not h.archetype.is_compileable:
                        continue

                    # TODO: this is redundant when machines are flushed as well,
                    # but should not hurt
                    if h.machine.id in interfaces_by_machine:
                        interfaces_by_machine[h.machine.id].sort(key=attrgetter('name'))
                        set_committed_value(h.machine, 'interfaces',
                                            interfaces_by_machine[h.machine.id])

                    try:
                        plenary_host = Plenary.get_plenary(h, logger=logger)
                        written += plenary_host.write(locked=True)
                    except IncompleteError, e:
                        pass
                        #logger.client_info("Not flushing host: %s" % e)
                    except Exception, e:
                        failed.append("{0} in {1:l} failed: {2}".format(h, h.branch, e))

            if clusters:
                logger.client_info("Flushing clusters.")
                q = session.query(Cluster)
                q = q.options(subqueryload('_hosts'),
                              joinedload('_hosts.host'),
                              joinedload('_hosts.host.machine'),
                              subqueryload('_metacluster'),
                              joinedload('_metacluster.metacluster'),
                              joinedload('resholder'),
                              subqueryload('resholder.resources'),
                              subqueryload('service_bindings'),
                              subqueryload('allowed_personalities'))
                cnt = q.count()
                idx = 0
                for clus in q:
                    idx += 1
                    if idx % 20 == 0:  # pragma: no cover
                        logger.client_info("Processing cluster %d of %d..." %
                                           (idx, cnt))
                    try:
                        plenary = Plenary.get_plenary(clus, logger=logger)
                        written += plenary.write(locked=True)
                    except Exception, e:
                        failed.append("{0} failed: {1}".format(clus, e))

            if resources:
                logger.client_info("Flushing resources.")

                q = session.query(Resource)
                cnt = q.count()
                idx = 0
                for dbresource in q:
                    idx += 1
                    if idx % 1000 == 0:  # pragma: no cover
                        logger.client_info("Processing resource %d of %d..." %
                                           (idx, cnt))
                    try:
                        plenary = Plenary.get_plenary(dbresource, logger=logger)
                        written += plenary.write(locked=True)
                    except Exception, e:
                        failed.append("{0} failed: {1}".format(dbresource, e))

            if switches or all:
                logger.client_info("Flushing switches.")
                for dbswitch in session.query(Switch).all():
                    try:
                        plenary = Plenary.get_plenary(dbswitch, logger=logger)
                        written += plenary.write(locked=True)
                    except Exception, e:
                        failed.append("{0} failed: {1}".format(dbswitch, e))

            # written + len(failed) isn't actually the total that should
            # have been done, but it's the easiest to implement for this
            # count and should be reasonably close... :)
            logger.client_info("Flushed %d/%d templates." %
                               (written, written + len(failed)))
            if failed:
                raise PartialError(success, failed)

        return
