# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
import gc
from six import iteritems

from sqlalchemy.orm import (joinedload, subqueryload, lazyload, contains_eager,
                            undefer)
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.sql import and_

from aquilon.exceptions_ import PartialError, IncompleteError
from aquilon.aqdb.model import (Service, Machine, Chassis, Host,
                                PersonalityStage, Archetype, Cluster, City,
                                Rack, Bunker, Building, Resource, HostResource,
                                ClusterResource, BundleResource, VirtualMachine,
                                Filesystem, ServiceAddress, Share, Disk, Model,
                                Interface, AddressAssignment, Network,
                                NetworkEnvironment, NetworkCompartment,
                                ServiceInstance, HardwareEntity, NetworkDevice,
                                RouterAddress, VirtualSwitch,
                                PortGroup, ParamDefHolder, Feature)
from aquilon.aqdb.data_sync.storage import StormapParser
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.switchdata import PlenarySwitchData
from aquilon.worker.locks import CompileKey
from aquilon.utils import ProgressReport


class CommandFlush(BrokerCommand):

    def preload_resources(self, session, res_cache, holder_cache, classes=None):
        # Load the most common resource types. Using
        # with_polymorphic('*') on Resource would generate a huge query,
        # so do something more targeted.
        extra_options = {
            BundleResource: [joinedload('resourcegroup')],
            ServiceAddress: [joinedload('dns_record'),
                             subqueryload('interfaces')],
            VirtualMachine: [joinedload('machine'),
                             joinedload('machine.primary_name'),
                             joinedload('machine.primary_name.fqdn'),
                             joinedload('machine.host'),
                             subqueryload('machine.host.personality_stage'),
                             joinedload('machine.host.personality_stage.personality'),
                             lazyload('machine.host.branch')],
        }

        if not classes:
            classes = Resource.__subclasses__()

        if Share in classes:
            parser = StormapParser()

        for cls in classes:
            q = session.query(cls)
            q = q.options(joinedload('holder'))
            if cls in extra_options:
                q = q.options(*extra_options[cls])

            for res in q:
                res_cache[res.id] = res

                if res.holder_id not in holder_cache:
                    holder_cache[res.holder_id] = res.holder

                if isinstance(res, Share):
                    res.populate_share_info(parser)

    def preload_interfaces(self, session, hosts, interfaces_by_id,
                           interfaces_by_hwent):
        addrs_by_iface = defaultdict(list)
        slaves_by_id = defaultdict(list)

        # Polymorphic loading cannot be applied to eager-loaded
        # attributes, so load interfaces manually.
        q = session.query(Interface)
        q = q.with_polymorphic('*')
        for iface in q:
            interfaces_by_hwent[iface.hardware_entity_id].append(iface)
            interfaces_by_id[iface.id] = iface
            if iface.master_id:
                slaves_by_id[iface.master_id].append(iface)

        # subqueryload() and with_polymorphic() do not play nice
        # together, so do it by hand
        q = session.query(AddressAssignment)
        q = q.options(joinedload("network"),
                      joinedload("dns_records"))
        q = q.order_by(AddressAssignment.label)

        if hosts:
            q = q.options(subqueryload("network.static_routes"),
                          subqueryload("network.routers"))

        for addr in q:
            addrs_by_iface[addr.interface_id].append(addr)

        for iface_id, iface in iteritems(interfaces_by_id):
            set_committed_value(iface, "assignments",
                                addrs_by_iface.get(iface_id, None))
            set_committed_value(iface, "slaves",
                                slaves_by_id.get(iface_id, None))

    def render(self, session, logger, services, personalities, machines,
               clusters, hosts, locations, resources, networks, network_devices,
               virtual_switches, all, **arguments):
        if all:
            services = True
            personalities = True
            machines = True
            clusters = True
            hosts = True
            locations = True
            resources = True
            network_devices = True
            virtual_switches = True
            networks = True

        with CompileKey(logger=logger):
            logger.client_info("Loading data.")

            success = []
            failed = []
            written = 0

            # Caches for keeping preloaded data pinned in memory, since the SQLA
            # session holds a weak reference only
            resource_by_id = {}
            resholder_by_id = {}
            service_instances = None  # pylint: disable=W0612
            racks = None  # pylint: disable=W0612
            models = None  # pylint: disable=W0612

            # Object caches that are accessed directly
            disks_by_machine = defaultdict(list)
            interfaces_by_hwent = defaultdict(list)
            interfaces_by_id = {}

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
                q = q.options(contains_eager('host'),
                              joinedload('host.hardware_entity'))
                for resholder in q:
                    resholder_by_id[resholder.id] = resholder

            if hosts or clusters or resources or machines:
                # Most machines are in racks...
                q = session.query(Rack)
                q = q.options(subqueryload("dns_maps"),
                              lazyload("dns_maps.location"),
                              subqueryload("parents"),
                              subqueryload("parents.dns_maps"),
                              lazyload("parents.dns_maps.location"))
                racks = q.all()

            if machines or resources:
                # Loading all models is cheaper than any filtering
                models = session.query(Model).options(joinedload('vendor')).all()

            if hosts or clusters or resources:
                self.preload_resources(session, resource_by_id, resholder_by_id)
            elif machines:
                self.preload_resources(session, resource_by_id, resholder_by_id,
                                       [Share, Filesystem])

            if hosts or machines:
                self.preload_interfaces(session, hosts, interfaces_by_id,
                                        interfaces_by_hwent)

            if hosts or services:
                q = session.query(ServiceInstance)
                q = q.options(subqueryload("service"))
                service_instances = q.all()

            if locations:
                logger.client_info("Flushing locations.")
                q = session.query(City)
                q = q.options(subqueryload('parents'))
                for dbloc in q:
                    try:
                        plenary = Plenary.get_plenary(dbloc, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbloc, e))
                        continue

            if services:
                logger.client_info("Flushing services.")
                q = session.query(Service)
                q = q.options(subqueryload("instances"),
                              lazyload("instances.service"),
                              subqueryload("instances.servers"),
                              subqueryload("instances.servers.host"),
                              joinedload("instances.servers.host.hardware_entity"))
                progress = ProgressReport(logger, q.count(), "service")
                for dbservice in q:
                    progress.step()
                    try:
                        plenary_info = Plenary.get_plenary(dbservice,
                                                           logger=logger)
                        written += plenary_info._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbservice, e))
                        continue

                    for dbinst in dbservice.instances:
                        try:
                            plenary_info = Plenary.get_plenary(dbinst,
                                                               logger=logger)
                            written += plenary_info._write()
                        except Exception as e:
                            failed.append("{0} failed: {1}".format(dbinst, e))
                            continue

            if personalities:
                logger.client_info("Flushing personalities.")

                q = session.query(Feature)
                q = q.with_polymorphic('*')
                q = q.options(joinedload('param_def_holder'),
                              undefer('comments'))
                features = q.all()  # pylint: disable=W0612

                q = session.query(Archetype)
                q = q.options(subqueryload('features'),
                              subqueryload('param_def_holders'))
                archetypes = q.all()  # pylint: disable=W0612

                q = session.query(ParamDefHolder)
                q = q.options(subqueryload('param_definitions'))
                paramdefs = q.all()  # pylint: disable=W0612

                q = session.query(PersonalityStage)
                q = q.options(joinedload('personality'),
                              subqueryload('grns'),
                              subqueryload('features'),
                              joinedload('parameter'),
                              subqueryload('personality.root_users'),
                              subqueryload('personality.root_netgroups'))
                progress = ProgressReport(logger, q.count(), "personality")
                for persst in q:
                    progress.step()
                    try:
                        plenary_info = Plenary.get_plenary(persst,
                                                           logger=logger)
                        written += plenary_info._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(persst, e))
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
                chassis = q.all()  # pylint: disable=W0612

                q = session.query(PortGroup)
                q = q.options(subqueryload('legacy_vlan'))
                port_groups = q.all()  # pylint: disable=W0612

                q = session.query(Machine)
                q = q.options(lazyload("primary_name"),
                              subqueryload("chassis_slot"))

                progress = ProgressReport(logger, q.count(), "machine")
                for machine in q:
                    progress.step()

                    set_committed_value(machine, 'disks',
                                        disks_by_machine.get(machine.id, None))
                    set_committed_value(machine, 'interfaces',
                                        interfaces_by_hwent.get(machine.id, None))

                    try:
                        plenary_info = Plenary.get_plenary(machine,
                                                           logger=logger)
                        written += plenary_info._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(machine, e))
                        continue

            if hosts:
                logger.client_info("Flushing hosts.")

                q = session.query(Cluster)
                q = q.options(subqueryload("metacluster"),
                              lazyload("location_constraint"),
                              lazyload("personality_stage"),
                              lazyload("branch"))
                cluster_cache = q.all()  # pylint: disable=W0612

                q = session.query(Host)
                q = q.options(joinedload("hardware_entity"),
                              joinedload("hardware_entity.primary_name"),
                              joinedload("hardware_entity.primary_name.fqdn"),
                              subqueryload("grns"),
                              joinedload("resholder"),
                              subqueryload("resholder.resources"),
                              subqueryload("services_used"),
                              subqueryload("services_provided"),
                              subqueryload("_cluster"),
                              subqueryload("personality_stage"),
                              joinedload("personality_stage.personality"),
                              subqueryload("personality_stage.grns"),
                              subqueryload("personality_stage.required_services"),
                              subqueryload("virtual_switch"))

                progress = ProgressReport(logger, q.count(), "host")
                for h in q:
                    progress.step()

                    if not h.archetype.is_compileable:
                        continue

                    # TODO: this is redundant when machines are flushed as well,
                    # but should not hurt
                    set_committed_value(h.hardware_entity, 'interfaces',
                                        interfaces_by_hwent.get(h.hardware_entity.id, None))

                    try:
                        plenary_host = Plenary.get_plenary(h, logger=logger)
                        written += plenary_host._write()
                    except IncompleteError as e:
                        pass
                        # logger.client_info("Not flushing host: %s" % e)
                    except Exception as e:
                        failed.append("{0} in {1:l} failed: {2}".format(h, h.branch, e))

            if clusters:
                logger.client_info("Flushing clusters.")
                q = session.query(Cluster)
                q = q.with_polymorphic('*')
                q = q.options(subqueryload('_hosts'),
                              joinedload('_hosts.host'),
                              joinedload('_hosts.host.hardware_entity'),
                              subqueryload('metacluster'),
                              joinedload('resholder'),
                              subqueryload('resholder.resources'),
                              subqueryload('services_used'),
                              subqueryload('services_provided'),
                              subqueryload('allowed_personalities'),
                              subqueryload('virtual_switch'))
                progress = ProgressReport(logger, q.count(), "cluster")
                for clus in q:
                    progress.step()
                    try:
                        plenary = Plenary.get_plenary(clus, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(clus, e))

            if resources:
                logger.client_info("Flushing resources.")

                q = session.query(Resource.id)
                progress = ProgressReport(logger, q.count(), "resource")
                for resid in q:
                    progress.step()
                    dbresource = session.query(Resource).get(resid)
                    try:
                        plenary = Plenary.get_plenary(dbresource, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbresource, e))

            if networks:
                logger.client_info("Flushing networks.")

                # pylint: disable=W0612
                compartments = session.query(NetworkCompartment).all()

                # pylint: disable=W0612
                envs = session.query(NetworkEnvironment).all()

                # Load the most common location types
                q = session.query(Building)
                q = q.options(subqueryload('parents'))
                buildings = q.all()  # pylint: disable=W0612
                q = session.query(Bunker)
                q = q.options(subqueryload('parents'))
                bunkers = q.all()  # pylint: disable=W0612

                q = session.query(HardwareEntity)
                q = q.join(Interface, AddressAssignment)
                q = q.join((RouterAddress, and_(AddressAssignment.network_id == RouterAddress.network_id,
                                                AddressAssignment.ip == RouterAddress.ip)))
                q = q.options(subqueryload('interfaces'),
                              subqueryload('interfaces.assignments'),
                              joinedload('primary_name'))
                routers = q.all()  # pylint: disable=W0612

                q = session.query(Network)
                q = q.options(subqueryload('routers'),
                              subqueryload('routers.dns_records'))
                progress = ProgressReport(logger, q.count(), "networks")
                for dbnetwork in q:
                    progress.step()
                    try:
                        plenary = Plenary.get_plenary(dbnetwork, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbnetwork, e))

            if network_devices:
                logger.client_info("Flushing network devices.")
                q = session.query(NetworkDevice)
                q = q.options(subqueryload('interfaces'),
                              subqueryload('port_groups'),
                              joinedload('port_groups.network'))
                progress = ProgressReport(logger, q.count(), "network device")
                for dbnetdev in q:
                    progress.step()
                    try:
                        plenary = PlenarySwitchData.get_plenary(dbnetdev, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbnetdev, e))
                    try:
                        plenary = Plenary.get_plenary(dbnetdev, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbnetdev, e))

            if virtual_switches:
                logger.client_info("Flushing virtual switches.")
                q = session.query(VirtualSwitch)
                q = q.options(subqueryload("port_groups"),
                              joinedload("port_groups.network"),
                              joinedload("port_groups.legacy_vlan"))
                progress = ProgressReport(logger, q.count(), "virtual switch")
                for dbvswitch in q:
                    progress.step()
                    try:
                        plenary = Plenary.get_plenary(dbvswitch, logger=logger)
                        written += plenary._write()
                    except Exception as e:
                        failed.append("{0} failed: {1}".format(dbvswitch, e))

            # written + len(failed) isn't actually the total that should
            # have been done, but it's the easiest to implement for this
            # count and should be reasonably close... :)
            logger.client_info("Flushed %d/%d templates." %
                               (written, written + len(failed)))
            if failed:
                raise PartialError(success, failed)

        session.expunge_all()
        gc.collect()

        return
