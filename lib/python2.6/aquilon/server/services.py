# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Provides various utilities around services."""


import logging
from random import choice

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, InternalError, IncompleteError
from aquilon.aqdb.model import (Host, Cluster, BuildItem, ServiceMap,
                                PersonalityServiceMap, ClusterServiceBinding,
                                ClusterAlignedService, ServiceInstance)
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.base import PlenaryCollection


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
        return chooser

    # Technically apply_changes is a method, but whatever...
    abstract_fields = ["description", "archetype", "personality", "location",
                       "required_services", "original_service_instances",
                       "apply_changes"]

    def __init__(self, dbobj, logger, required_only=False):
        """Initialize the chooser.

        To clear out bindings that are not required, pass in
        required_only=True.

        Several staging areas and caches are set up within this object.
        The general flow is that potential service instance choices
        are kept in staging_services (dictionary of service to list of
        service instances) and finalized into chosen_services (dictionary
        of service to single service instance).

        The original state of the object is held in the caches
        original_service_build_items (list of build items, but only
        services) and original_service_instances (dictionary of
        service to single service instance).

        The instances_bound and instances_unbound lists are populated
        after chosen_services with the differences between chosen_services
        and original_service_instances.

        Subclasses should call this before starting their own
        initialization.

        """
        self.dbobj = dbobj
        self.session = object_session(dbobj)
        self.required_only = required_only
        self.logger = logger
        self.description = self.generate_description()
        self.logger.debug("Creating service Chooser for %s", self.description)
        # Cache of the service maps
        self.mapped_services = {}
        self.staging_services = {}
        """Stores interim service instance lists."""
        self.errors = []
        """Report as many errors as possible in one shot."""
        self.servers = {}
        """Cache the servers backing service instances."""
        self.instances_bound = set()
        """Set of service instances with a new client."""
        self.instances_unbound = set()
        """Set of service instances losing a client."""
        self.chosen_services = {}
        """Track the chosen services."""
        self.plenaries = PlenaryCollection(logger=self.logger)
        """Keep stashed plenaries for rollback purposes."""

    def generate_description(self):
        return str(self.dbobj)

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
            cfg_path = list(self.instances_unbound)[0].cfg_path
            self.error("%s is already bound to %s, use unbind "
                       "to clear first or rebind to force." %
                       (self.description, cfg_path))
            self.check_errors()
        self.stash_services()
        self.apply_changes()
        self.check_errors()

    def cache_service_maps(self, dbservices):
        self.service_maps = ServiceInstance.get_mapped_instance_cache(
            self.personality, self.location, dbservices)

    def find_service_instances(self, dbservice):
        """This finds the "closest" service instances, based on the known maps.

        It expects that cache_service_maps has been run.

        """
        instances = self.service_maps.get(dbservice, [])
        if len(instances) >= 1:
            for instance in instances:
                self.logger.debug("Found service %s instance %s "
                                  "in the maps.",
                                  instance.service.name, instance.name)
            self.staging_services[dbservice] = instances
            return
        self.error("Could not find a relevant service map for service %s "
                   "on %s", dbservice.name, self.description)

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
           self.original_service_instances.get(dbservice, None) and \
           self.original_service_instances[dbservice] in \
           self.staging_services[dbservice]:
            self.logger.debug("Chose service %s instance %s because "
                              "of past use.",
                              dbservice.name,
                              self.original_service_instances[dbservice])
            self.staging_services[dbservice] = [
                self.original_service_instances[dbservice]]
        return

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
            for host in instances[0].server_hosts:
                if self.servers.get(host, None):
                    self.servers[host] += 1
                else:
                    self.servers[host] = 1

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
        max_instances = None
        for instance in self.staging_services[dbservice]:
            common_servers = []
            self.logger.debug("Checking service %s instance %s servers %s",
                              instance.service.name, instance.name,
                              [host.fqdn for host in instance.server_hosts])
            for host in instance.server_hosts:
                if self.servers.get(host, None):
                    common_servers.append(host)
            if not common_servers:
                continue
            if len(common_servers) > max_servers:
                max_servers = len(common_servers)
                max_instances = [instance]
            elif len(common_servers) == max_servers:
                max_instances.append(instance)
        if max_instances and \
           len(max_instances) < len(self.staging_services[dbservice]):
            for instance in self.staging_services[dbservice]:
                if instance not in max_instances:
                    self.logger.debug("Discounted service %s instance %s "
                                      "due to server affinity (stickiness).",
                                      instance.service.name, instance.name)
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
                    self.logger.debug("Discounted service %s instance %s "
                                      "due to load.",
                                      instance.service.name, instance.name)
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
            if not self.original_service_instances.get(service, None) or \
               self.original_service_instances[service] != instance:
                self.instances_bound.add(instance)
        for (service, instance) in self.original_service_instances.items():
            if not self.chosen_services.get(service, None) or \
               self.chosen_services[service] != instance:
                self.instances_unbound.add(instance)

    def stash_services(self):
        for instance in self.instances_bound.union(self.instances_unbound):
            plenary = PlenaryServiceInstanceServer(instance.service, instance,
                                                   logger=self.logger)
            plenary.stash()
            self.plenaries.append(plenary)

    def flush_changes(self):
        self.session.flush()

    def get_write_key(self):
        return self.plenaries.get_write_key()

    def write_plenary_templates(self, locked=False):
        self.plenaries.write(locked=locked)

    def prestash_primary(self):
        pass

    def restore_stash(self):
        self.plenaries.restore_stash()


class HostChooser(Chooser):
    """Choose services for a host."""

    def __init__(self, dbobj, *args, **kwargs):
        """Provide initialization specific for host bindings."""
        if not isinstance(dbobj, Host):
            raise InternalError("HostChooser can only choose services for "
                                "hosts, got %r (%s)" % (dbobj, type(dbobj)))
        self.dbhost = dbobj
        Chooser.__init__(self, dbobj, *args, **kwargs)
        self.location = self.dbhost.machine.location
        self.archetype = self.dbhost.archetype
        self.personality = self.dbhost.personality
        self.required_services = set()
        """Stores interim service instance lists."""
        for service in self.archetype.services:
            self.required_services.add(service)
        for service in self.personality.services:
            self.required_services.add(service)
        q = self.session.query(BuildItem).filter_by(host=self.dbhost)
        self.original_service_build_items = q.all()
        """Cache of the build_items related to services."""
        self.original_service_instances = {}
        """Cache of any already bound services (keys) and the instance
        that was bound (values).
        """
        for dbbi in self.original_service_build_items:
            self.original_service_instances[dbbi.service_instance.service] = \
                    dbbi.service_instance
            self.logger.debug("%s original binding: %s",
                              self.description, dbbi.cfg_path)
        self.cluster_aligned_services = {}
        if self.dbhost.cluster:
            # Note that cluster services are currently ignored unless
            # they are otherwise required by the archetype/personality.
            for si in self.dbhost.cluster.service_bindings:
                self.cluster_aligned_services[si.service] = si
            q = self.session.query(ClusterAlignedService)
            q = q.filter_by(cluster_type=self.dbhost.cluster.cluster_type)
            for item in q.all():
                if item.service not in self.cluster_aligned_services:
                    # Don't just error here because the error() call
                    # has not yet been set up.  Will error out later.
                    self.cluster_aligned_services[item.service] = None
                # Went back and forth on this... deciding not to force
                # an aligned service as required.  This should give
                # flexibility for multiple services to be aligned for
                # a cluster type without being forced on all the
                # personalities.
                #self.required_services.add(item.service)

    def generate_description(self):
        return format(self.dbhost)

    def choose_cluster_aligned(self, dbservice):
        if dbservice not in self.cluster_aligned_services:
            return
        if not self.cluster_aligned_services[dbservice]:
            self.error("No instance set for %s aligned service %s."
                       "  Please run `make cluster --cluster %s` to resolve.",
                       format(self.dbhost.cluster),
                       dbservice.name,
                       self.dbhost.cluster.name)
            return
        # This check is necessary to prevent bind_client from overriding
        # the cluster's binding.  The error message will be misleading...
        if self.cluster_aligned_services[dbservice] not in \
           self.staging_services[dbservice]:
            self.error("{0} is set to use {1:l}, but that instance is not in a "
                       "service map for {2}.".format(self.dbhost.cluster,
                                                     self.cluster_aligned_services[dbservice],
                                                     self.dbhost.fqdn))
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
            self.logger.client_info("%s adding binding for service %s "
                                    "instance %s",
                                    self.description,
                                    instance.service.name, instance.name)
            if self.original_service_instances.get(instance.service, None):
                previous = None
                for bi in self.original_service_build_items:
                    if bi.service_instance and \
                       bi.service_instance.service == instance.service:
                        previous = bi
                        break
                if previous:
                    previous.service_instance = instance
                else:
                    self.error("Internal Error: Error in alogorithm to find "
                               "previous binding for %s %s" %
                               (instance.service.name, instance.name))
                continue
            bi = BuildItem(host=self.dbhost, service_instance=instance)
            self.dbhost.services_used.append(bi)
        for instance in self.instances_unbound:
            self.logger.client_info("%s removing binding for "
                                    "service %s instance %s",
                                    self.description,
                                    instance.service.name, instance.name)
            if self.chosen_services.get(instance.service, None):
                # We have a replacement, no need to remove BuildItem
                continue
            found_instance = False
            for bi in self.original_service_build_items:
                if bi.service_instance == instance:
                    self.session.delete(bi)
                    found_instance = True
                    break
            if not found_instance:
                self.error("Internal Error: Could not unbind "
                           "service %s instance %s" %
                           (instance.service.name, instance.name))
        if self.instances_bound or self.instances_unbound:
            # Can't use _reorder if missing os, as adding the os later
            # will fail.
            # It may make sense to never call reorder()...
            #if self.dbhost.services_used and \
            #   self.dbhost.services_used[0].cfg_path.tld.type == 'os':
            #    self.dbhost.services_used._reorder()
            self.session.add(self.dbhost)

    def prestash_primary(self):
        plenary_host = PlenaryHost(self.dbhost, logger=self.logger)
        plenary_host.stash()
        self.plenaries.append(plenary_host)


class ClusterChooser(Chooser):
    """Choose services for a cluster."""

    def __init__(self, dbobj, *args, **kwargs):
        """Provide initialization specific for cluster bindings."""
        if not isinstance(dbobj, Cluster):
            raise InternalError("ClusterChooser can only choose services for "
                                "clusters, got %r (%s)" % (dbobj, type(dbobj)))
        self.dbcluster = dbobj
        Chooser.__init__(self, dbobj, *args, **kwargs)
        self.location = self.dbcluster.location_constraint
        self.archetype = self.dbcluster.personality.archetype
        self.personality = self.dbcluster.personality
        self.required_services = set()
        """Stores interim service instance lists."""
        q = self.session.query(ClusterAlignedService)
        q = q.filter_by(cluster_type=self.dbcluster.cluster_type)
        for item in q.all():
            self.required_services.add(item.service)
        self.original_service_instances = {}
        """Cache of any already bound services (keys) and the instance
        that was bound (values).
        """
        for si in self.dbcluster.service_bindings:
            self.original_service_instances[si.service] = si
            self.logger.debug("%s original binding: %s",
                              self.description, si.cfg_path)

    def generate_description(self):
        return format(self.dbcluster)

    def get_footprint(self, instance):
        """If this cluster is bound to a service, how many hosts bind?"""
        cluster_types = instance.service.aligned_cluster_types
        if self.dbcluster.cluster_type in cluster_types:
            return self.dbcluster.max_hosts
        return 0

    def apply_changes(self):
        """Update the cluster object with pending changes."""
        for instance in self.instances_unbound:
            self.logger.client_info("%s removing binding for "
                                    "service %s instance %s",
                                    self.description,
                                    instance.service.name, instance.name)
            dbcs = ClusterServiceBinding.get_unique(self.session,
                                                    cluster=self.dbcluster,
                                                    service_instance=instance)
            if dbcs:
                self.session.delete(dbcs)
            else:
                self.error("Internal Error: Could not unbind "
                           "service %s instance %s" %
                           (instance.service.name, instance.name))
        for instance in self.instances_bound:
            self.logger.client_info("%s adding binding for "
                                    "service %s instance %s",
                                    self.description,
                                    instance.service.name, instance.name)
            dbcs = ClusterServiceBinding(cluster=self.dbcluster,
                                         service_instance=instance)
            self.session.add(dbcs)
            self.flush_changes()
            for h in self.dbcluster.hosts:
                host_plenary = PlenaryHost(h, logger=self.logger)
                host_plenary.stash()
                self.plenaries.append(host_plenary)
                host_chooser = Chooser(h, logger=self.logger,
                                       required_only=False)
                host_chooser.set_single(instance.service, instance, force=True)
                host_chooser.flush_changes()
                # Note, host plenary will be written later.

    def prestash_primary(self):
        plenary_cluster = PlenaryCluster(self.dbcluster, logger=self.logger)
        plenary_cluster.stash()
        self.plenaries.append(plenary_cluster)
