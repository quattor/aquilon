# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Provides various utilities around services."""

from random import choice

from sqlalchemy.orm import undefer
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql import or_

from aquilon.exceptions_ import ArgumentError, InternalError
from aquilon.aqdb.model import (Host, Cluster, Service, ServiceInstance,
                                MetaCluster, EsxCluster, Archetype, Personality)
from aquilon.worker.templates import (Plenary, PlenaryCollection,
                                      PlenaryServiceInstanceServer)


class Chooser(object):
    """Helper for choosing services for an object."""

    def __new__(cls, dbobj, *args, **kwargs):
        if isinstance(dbobj, Host):
            chooser = super(Chooser, HostChooser).__new__(HostChooser)
        elif isinstance(dbobj, Cluster):
            chooser = super(Chooser, ClusterChooser).__new__(ClusterChooser)
        else:
            # Just assume the consumer invoked the right subclass...
            chooser = super(Chooser, cls).__new__(cls)

        # Lock the owner in the DB to avoid problems with parallel runs
        dbobj.lock_row()

        return chooser

    abstract_fields = ["location", "required_services", "network",
                       "original_service_instances"]

    def __init__(self, dbobj, logger, required_only=False):
        """Initialize the chooser.

        To clear out bindings that are not required, pass in
        required_only=True.

        Several staging areas and caches are set up within this object.
        The general flow is that potential service instance choices
        are kept in staging_services (dictionary of service to list of
        service instances) and finalized into chosen_services (dictionary
        of service to single service instance).

        The original state of the object is held in the cache
        original_service_instances (dictionary of service to single service
        instance).

        The instances_bound and instances_unbound lists are populated
        after chosen_services with the differences between chosen_services
        and original_service_instances.

        Subclasses should call this before starting their own
        initialization.

        """
        self.dbobj = dbobj
        self.personality = dbobj.personality
        self.archetype = dbobj.personality.archetype
        self.session = object_session(dbobj)
        self.required_only = required_only
        self.logger = logger
        self.logger.debug("Creating service chooser for {0:l}"
                          .format(self.dbobj))
        # Cache of the service maps
        self.mapped_services = {}

        # Stores interim service instance lists
        self.staging_services = {}

        # Report as many errors as possible in one shot
        self.errors = []

        # Cache the servers backing service instances, used to determine
        # affinity
        self.servers = set()

        # Set of service instances with a new client
        self.instances_bound = set()

        # Set of service instances losing a client
        self.instances_unbound = set()

        # Track the chosen services
        self.chosen_services = {}

        # Keep stashed plenaries for rollback purposes
        self.plenaries = PlenaryCollection(logger=self.logger)

    def apply_changes(self):
        raise InternalError("This method must be overridden")

    def verify_init(self):
        """This is more of a verify-and-finalize method..."""
        for field in self.abstract_fields:
            if not hasattr(self, field):
                raise InternalError("%s provides no %s field" %
                                    (type(self.dbobj), field))
        # This can be tweaked...
        if not self.required_only:
            for (service, instance) in self.original_service_instances.items():
                self.staging_services[service] = [instance]

    def error(self, msg, *args, **kwargs):
        """Errors are consolidated so that many can be reported at once."""
        formatted = msg % args
        self.errors.append(formatted)
        self.logger.info(msg, *args, **kwargs)

    def set_required(self):
        """Main entry point when setting the required services for a host."""
        self.verify_init()
        self.prestash_primary()
        self.logger.debug("Setting required services")
        self.cache_service_maps(self.required_services)
        for dbservice in self.required_services:
            self.find_service_instances(dbservice)
        self.check_errors()
        for dbservice in self.required_services:
            self.choose_cluster_aligned(dbservice)
            self.choose_available_capacity(dbservice)
            self.choose_past_use(dbservice)
        self.check_errors()
        # If this code needs to be made more efficient, this could
        # be refactored.  We don't always need count_servers()...
        # In theory don't always need the loop above, either.
        self.count_servers()
        for dbservice in self.required_services:
            self.reduce_service_instances(dbservice)
        self.finalize_service_instances()
        self.analyze_changes()
        self.stash_services()
        self.apply_changes()
        self.check_errors()

    def set_single(self, service, instance=None, force=False):
        """Use this to update a single service.

        If planning to use this method, construct the Chooser with
        required_only=False.  If required_only is True, all other
        bindings will be cleared.

        """
        self.verify_init()
        self.prestash_primary()
        if instance:
            self.logger.debug("Setting service %s instance %s",
                              service.name, instance.name)
            self.staging_services[service] = [instance]
        else:
            self.logger.debug("Setting service %s with auto-bind",
                              service.name)
            self.staging_services[service] = None
            self.cache_service_maps([service])
            self.find_service_instances(service)
        self.check_errors()
        self.choose_cluster_aligned(service)
        self.choose_available_capacity(service)
        self.check_errors()
        self.choose_past_use(service)
        # If this code needs to be made more efficient, this could
        # be refactored.  We don't always need count_servers()...
        self.count_servers()
        self.reduce_service_instances(service)
        self.finalize_service_instances()
        self.analyze_changes()
        if not force and self.instances_bound and self.instances_unbound:
            si = list(self.instances_unbound)[0]
            self.error("{0} is already bound to {1:l}, use unbind "
                       "to clear first or rebind to force."
                       .format(self.dbobj, si))
            self.check_errors()
        self.stash_services()
        self.apply_changes()
        self.check_errors()

    def cache_service_maps(self, dbservices):
        self.service_maps = ServiceInstance.get_mapped_instance_cache(
            self.personality, self.location, dbservices, self.network)

    def find_service_instances(self, dbservice):
        """This finds the "closest" service instances, based on the known maps.

        It expects that cache_service_maps has been run.

        """
        instances = self.service_maps.get(dbservice, [])
        if len(instances) >= 1:
            for instance in instances:
                self.logger.debug("Found {0:l} in the maps.".format(instance))
            self.staging_services[dbservice] = instances
            return
        self.error("Could not find a relevant service map for {0:l} "
                   "on {1:l}".format(dbservice, self.dbobj))

    def check_errors(self):
        if self.errors:
            raise ArgumentError("\n".join(self.errors))

    def choose_cluster_aligned(self, dbservice):
        # Only implemented for hosts.
        pass

    def get_footprint(self, instance):
        return 1

    def instance_full(self, instance, max_clients, current_clients):
        """Check if the instance is effectively full.

        This check is complicated because clusters have a larger impact
        than a single host does.

        """
        if max_clients is None:
            return False
        if instance == self.original_service_instances.get(instance.service):
            if current_clients > max_clients:
                return True
            return False
        return current_clients + self.get_footprint(instance) > max_clients

    def choose_available_capacity(self, dbservice):
        """Verify that the available instances have spare capacity.

        Error out if none should be used.

        """
        maxed_out_instances = set()
        for instance in self.staging_services[dbservice][:]:
            max_clients = instance.enforced_max_clients
            current_clients = instance.client_count
            if self.instance_full(instance, max_clients, current_clients):
                self.staging_services[dbservice].remove(instance)
                maxed_out_instances.add(instance)
                self.logger.debug("Rejected service %s instance %s with "
                                  "max_client value of %s since client_count "
                                  "is %s.",
                                  instance.service.name, instance.name,
                                  max_clients, current_clients)
        if len(self.staging_services[dbservice]) < 1:
            self.error("The available instances %s for service %s are "
                       "at full capacity.",
                       [str(instance.name)
                        for instance in maxed_out_instances],
                       dbservice.name)
        return

    def choose_past_use(self, dbservice):
        """If more than one service instance was found in the maps,
        this method checks to see if we can reduce the list to a single
        choice by checking to see if any of the instances was already in use.

        """
        if len(self.staging_services[dbservice]) > 1 and \
           dbservice in self.original_service_instances and \
           self.original_service_instances[dbservice] in \
           self.staging_services[dbservice]:
            instance = self.original_service_instances[dbservice]
            self.logger.debug("Chose {0:l} because of past use."
                              .format(instance))
            self.staging_services[dbservice] = [instance]
        return

    def append_server_object(self, container, srv):
        """Append server objects to a container.

        This is a helper used for implementing server affinity.

        """
        if srv.host:
            container.add(srv.host)
        if srv.cluster:
            container.add(srv.cluster)

        # If the service is not bound to a host or cluster, then we have
        # no choice than to use the alias for providing server affinity
        if srv.alias and not srv.host and not srv.cluster:
            container.add(srv.alias)

    def count_servers(self, dbservice=None):
        """Get a count of the number of times a server backs
        service instances in use by this host.

        This method is called both to initialize the count and to update
        it as service instances are locked in.

        """
        if dbservice:
            instance_lists = [self.staging_services[dbservice]]
        else:
            instance_lists = self.staging_services.values()

        for instances in instance_lists:
            if len(instances) > 1:
                # Ignore any services where an instance has not been chosen.
                continue
            for srv in instances[0].servers:
                self.append_server_object(self.servers, srv)

    def reduce_service_instances(self, dbservice):
        if len(self.staging_services[dbservice]) == 1:
            self.count_servers(dbservice)
            return
        self.choose_affinity(dbservice)
        if len(self.staging_services[dbservice]) == 1:
            self.count_servers(dbservice)
            return
        self.choose_least_loaded(dbservice)
        if len(self.staging_services[dbservice]) == 1:
            self.count_servers(dbservice)
            return
        self.choose_random(dbservice)
        self.count_servers(dbservice)
        return

    def choose_affinity(self, dbservice):
        """Attempt to choose a service based on server affinity,
        also known as stickiness.

        This could be extremely complicated when trying to deal with
        instances backed by multiple servers.  Starting simple.
        Count the number of servers backing this instance that
        back other instances used by client.  Any instance that does
        not have the largest count gets tossed.

        """
        max_servers = 0
        max_instances = []
        for instance in self.staging_services[dbservice]:
            self.logger.debug("Checking service %s instance %s servers %s",
                              instance.service.name, instance.name,
                              [srv.fqdn for srv in instance.servers])
            instance_servers = set()
            for srv in instance.servers:
                self.append_server_object(instance_servers, srv)

            common_servers = self.servers & instance_servers
            if len(common_servers) > max_servers:
                max_servers = len(common_servers)
                max_instances = [instance]
            elif len(common_servers) == max_servers:
                max_instances.append(instance)
        if max_instances and \
           len(max_instances) < len(self.staging_services[dbservice]):
            for instance in self.staging_services[dbservice]:
                if instance not in max_instances:
                    self.logger.debug("Discounted {0:l} due to server affinity "
                                      "(stickiness).".format(instance))
            self.staging_services[dbservice] = max_instances

    def choose_least_loaded(self, dbservice):
        """Choose a service instance based on load."""
        least_clients = None
        least_loaded = []
        for instance in self.staging_services[dbservice]:
            client_count = instance.client_count
            if not least_loaded or client_count < least_clients:
                least_clients = client_count
                least_loaded = [instance]
            elif client_count == least_clients:
                least_loaded.append(instance)
        if len(least_loaded) < len(self.staging_services[dbservice]):
            for instance in self.staging_services[dbservice]:
                if instance not in least_loaded:
                    self.logger.debug("Discounted {0:l} due to load."
                                      .format(instance))
            self.staging_services[dbservice] = least_loaded

    def choose_random(self, dbservice):
        """Pick a service instance randomly."""
        self.staging_services[dbservice] = [
            choice(self.staging_services[dbservice])]
        self.logger.debug("Randomly chose service %s instance %s "
                          "from remaining choices.",
                          dbservice.name,
                          self.staging_services[dbservice][0].name)

    def finalize_service_instances(self):
        """Fill out the list of chosen services."""
        for (service, instances) in self.staging_services.items():
            if len(instances) < 1:  # pragma: no cover
                self.error("Internal Error: Attempt to finalize on "
                           "service %s without any candidates." %
                           service.name)
                continue
            if len(instances) > 1:  # pragma: no cover
                self.error("Internal Error: Attempt to finalize on "
                           "service %s with too many candidates %s." %
                           (service.name,
                            ["service %s instance %s" %
                             (instance.service.name, instance.name)
                             for instance in instances]))
            self.chosen_services[service] = instances[0]

    def analyze_changes(self):
        """Determine what changed."""
        for (service, instance) in self.chosen_services.items():
            if service not in self.original_service_instances or \
               self.original_service_instances[service] != instance:
                self.instances_bound.add(instance)
        for (service, instance) in self.original_service_instances.items():
            if service not in self.chosen_services or \
               self.chosen_services[service] != instance:
                self.instances_unbound.add(instance)

    def stash_services(self):
        changed_servers = set()
        for instance in self.instances_bound.union(self.instances_unbound):
            if not instance.service.need_client_list:
                continue

            for srv in instance.servers:
                if srv.host:
                    changed_servers.add(srv.host)
                if srv.cluster:
                    changed_servers.add(srv.cluster)

            plenary = PlenaryServiceInstanceServer.get_plenary(instance)
            self.plenaries.append(plenary)

        for dbobj in changed_servers:
            # Skip servers that do not have a profile
            if not dbobj.personality.archetype.is_compileable:
                continue

            # Skip servers that are in a different domain/sandbox
            if (dbobj.branch != self.dbobj.branch or
                dbobj.sandbox_author_id != self.dbobj.sandbox_author_id):
                continue

            self.plenaries.append(Plenary.get_plenary(dbobj))
            if isinstance(dbobj, Cluster):
                for dbhost in dbobj.hosts:
                    self.plenaries.append(Plenary.get_plenary(dbhost))

    def flush_changes(self):
        self.session.flush()

    def get_key(self):
        return self.plenaries.get_key()

    def write_plenary_templates(self, locked=False):
        self.plenaries.stash()
        self.plenaries.write(locked=locked)

    def prestash_primary(self):
        pass

    def restore_stash(self):
        self.plenaries.restore_stash()


class HostChooser(Chooser):
    """Choose services for a host."""

    def __init__(self, dbhost, *args, **kwargs):
        """Provide initialization specific for host bindings."""
        if not isinstance(dbhost, Host):
            raise InternalError("HostChooser can only choose services for "
                                "hosts, got %r (%s)" % (dbhost, type(dbhost)))
        super(HostChooser, self).__init__(dbhost, *args, **kwargs)
        self.location = dbhost.hardware_entity.location

        # If the primary name is a ReservedName, then it does not have a network
        # attribute
        if hasattr(dbhost.hardware_entity.primary_name, 'network'):
            self.network = dbhost.hardware_entity.primary_name.network
        else:
            self.network = None

        # all of them would be self. but that should be optimized
        # dbhost.hardware_entity.interfaces[x].assignments[y].network

        # Stores interim service instance lists.
        q = self.session.query(Service)
        q = q.outerjoin(Service.archetypes)
        q = q.reset_joinpoint()
        q = q.outerjoin(Service.personalities)
        q = q.filter(or_(Archetype.id == self.archetype.id,
                         Personality.id == self.personality.id))
        self.required_services = set(q.all())

        self.original_service_instances = {}
        # Cache of any already bound services (keys) and the instance
        # that was bound (values).
        q = self.session.query(ServiceInstance)
        q = q.options(undefer('_client_count'))
        q = q.filter(ServiceInstance.clients.contains(dbhost))
        set_committed_value(dbhost, 'services_used', q.all())
        for si in dbhost.services_used:
            self.original_service_instances[si.service] = si
            self.logger.debug("{0} original binding: {1}"
                              .format(self.dbobj, si))
        self.cluster_aligned_services = {}
        if dbhost.cluster:
            # Note that cluster services are currently ignored unless
            # they are otherwise required by the archetype/personality.
            for si in dbhost.cluster.service_bindings:
                self.cluster_aligned_services[si.service] = si
            for service in dbhost.cluster.required_services:
                if service not in self.cluster_aligned_services:
                    # Don't just error here because the error() call
                    # has not yet been set up.  Will error out later.
                    self.cluster_aligned_services[service] = None
                # Went back and forth on this... deciding not to force
                # an aligned service as required.  This should give
                # flexibility for multiple services to be aligned for
                # a cluster type without being forced on all the
                # personalities.
                #self.required_services.add(item.service)

            if dbhost.cluster.metacluster:
                mc = dbhost.cluster.metacluster
                for si in mc.service_bindings:
                    if si.service in self.cluster_aligned_services:
                        cas = self.cluster_aligned_services[si.service]
                        if cas == None:
                            # Error out later.
                            continue

                        self.logger.client_info(
                            "Replacing {0.name} instance with {1.name} "
                            "(bound to {2:l}) for service {3.name}".format(
                            cas, si, mc, si.service))

                    self.cluster_aligned_services[si.service] = si
                for service in mc.required_services:
                    if service not in self.cluster_aligned_services:
                        # Don't just error here because the error() call
                        # has not yet been set up.  Will error out later.
                        self.cluster_aligned_services[service] = None

    def choose_cluster_aligned(self, dbservice):
        if dbservice not in self.cluster_aligned_services:
            return
        if not self.cluster_aligned_services[dbservice]:
            self.error("No instance set for %s aligned service %s."
                       "  Please run `make cluster --cluster %s` to resolve.",
                       format(self.dbobj.cluster),
                       dbservice.name,
                       self.dbobj.cluster.name)
            return
        # This check is necessary to prevent bind_client from overriding
        # the cluster's binding.  The error message will be misleading...
        if self.cluster_aligned_services[dbservice] not in \
           self.staging_services[dbservice]:
            self.error("{0} is set to use {1:l}, but that instance is not in a "
                       "service map for {2}.".format(self.dbobj.cluster,
                                                     self.cluster_aligned_services[dbservice],
                                                     self.dbobj.fqdn))
            return
        self.logger.debug("Chose service %s instance %s because it is cluster "
                          "aligned.",
                          dbservice.name,
                          self.cluster_aligned_services[dbservice].name)
        self.staging_services[dbservice] = [
            self.cluster_aligned_services[dbservice]]
        return

    def apply_changes(self):
        """Update the host object with pending changes."""
        for instance in self.instances_bound:
            self.logger.client_info("{0} adding binding for {1:l}"
                                    .format(self.dbobj, instance))
            self.dbobj.services_used.append(instance)
        for instance in self.instances_unbound:
            self.logger.client_info("{0} removing binding for {1:l}"
                                    .format(self.dbobj, instance))
            self.dbobj.services_used.remove(instance)

    def prestash_primary(self):
        self.plenaries.append(Plenary.get_plenary(self.dbobj))

        # This may be too much action at a distance... however, if
        # we are potentially re-writing a host plenary, it seems like
        # a good idea to also verify and refresh known dependencies.
        self.plenaries.append(Plenary.get_plenary(self.dbobj.hardware_entity))
        if self.dbobj.resholder:
            for dbres in self.dbobj.resholder.resources:
                self.plenaries.append(Plenary.get_plenary(dbres))


class ClusterChooser(Chooser):
    """Choose services for a cluster."""

    def __init__(self, dbcluster, *args, **kwargs):
        """Provide initialization specific for cluster bindings."""
        if not isinstance(dbcluster, Cluster):
            raise InternalError("ClusterChooser can only choose services for "
                                "clusters, got %r (%s)" % (dbcluster, type(dbcluster)))
        super(ClusterChooser, self).__init__(dbcluster, *args, **kwargs)
        self.location = dbcluster.location_constraint
        self.required_services = set()
        # TODO Should be calculated from member host's network membership.
        self.network = None
        # Stores interim service instance lists.
        for service in self.archetype.services:
            self.required_services.add(service)
        for service in self.personality.services:
            self.required_services.add(service)

        self.original_service_instances = {}
        # Cache of any already bound services (keys) and the instance
        # that was bound (values).
        for si in dbcluster.service_bindings:
            self.original_service_instances[si.service] = si
            self.logger.debug("{0} original binding: {1:l}"
                              .format(dbcluster, si))

    def get_footprint(self, instance):
        """If this cluster is bound to a service, how many hosts bind?"""
        if self.dbobj.personality in instance.service.personalities or \
            self.dbobj.personality.archetype in instance.service.archetypes:
            if self.dbobj.cluster_type == 'meta':
                return 0
            return self.dbobj.max_hosts
        return 0

    def apply_changes(self):
        """Update the cluster object with pending changes."""
        for instance in self.instances_unbound:
            self.logger.client_info("{0} removing binding for {1:l}"
                                    .format(self.dbobj, instance))
            if instance in self.dbobj.service_bindings:
                self.dbobj.service_bindings.remove(instance)
            else:
                self.error("Internal Error: Could not unbind {0:l}"
                           .format(instance))
        for instance in self.instances_bound:
            self.logger.client_info("{0} adding binding for {1:l}"
                                    .format(self.dbobj, instance))
            self.dbobj.service_bindings.append(instance)
            self.flush_changes()
            for h in self.dbobj.hosts:
                host_chooser = Chooser(h, logger=self.logger,
                                       required_only=False)
                host_chooser.set_single(instance.service, instance, force=True)
                host_chooser.flush_changes()
                # Note, host plenary will be written later.

    def prestash_primary(self):
        def add_cluster_dependencies(cluster):
            self.plenaries.append(Plenary.get_plenary(cluster))

            for dbhost in cluster.hosts:
                self.plenaries.append(Plenary.get_plenary(dbhost))

            if cluster.resholder:
                for dbres in cluster.resholder.resources:
                    self.plenaries.append(Plenary.get_plenary(dbres))

            if isinstance(cluster, EsxCluster) and cluster.network_device:
                self.plenaries.append(Plenary.get_plenary(cluster.network_device))

        add_cluster_dependencies(self.dbobj)

        if isinstance(self.dbobj, MetaCluster):
            for cluster in self.dbobj.members:
                add_cluster_dependencies(cluster)
