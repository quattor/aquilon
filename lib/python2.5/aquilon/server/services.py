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
"""Provides various utilities around services."""


import logging
from random import choice

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, InternalError, IncompleteError
from aquilon.aqdb.model import (Host, Cluster, Tld, BuildItem, ServiceMap,
                                PersonalityServiceMap, ClusterServiceBinding,
                                ClusterAlignedService)
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.base import compileLock, compileRelease


log = logging.getLogger('aquilon.server.services')

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

    def __init__(self, dbobj, required_only=False, debug=False):
        """Initialize the chooser.

        To clear out bindings that are not required, pass in
        required_only=True.

        If the debug flag is set to True, debug output will be
        gathered in an array for later use by the calling code.

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
        initialization.  At the very least, this must be called to use some
        common methods, like debug() and error().

        """
        self.dbobj = dbobj
        self.session = object_session(dbobj)
        self.is_debug_enabled = debug
        self.required_only = required_only
        self.debug_info = []
        """Store debug information."""
        self.description = self.generate_description()
        self.debug("Creating service Chooser for %s", self.description)
        self.staging_services = {}
        """Stores interim service instance lists."""
        self.messages = []
        """Report info-level log messages."""
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
        self.stashed = []
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

    def debug(self, msg, *args, **kwargs):
        if self.is_debug_enabled:
            self.debug_info.append(msg % args)
        log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Store status messages of interest to users."""
        formatted = msg % args
        if self.is_debug_enabled:
            self.debug_info.append(formatted)
        self.messages.append(formatted)
        log.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Errors are consolidated so that many can be reported at once."""
        formatted = msg % args
        if self.is_debug_enabled:
            self.debug_info.append(formatted)
        self.errors.append(formatted)
        log.error(msg, *args, **kwargs)

    def set_required(self):
        """Main entry point when setting the required services for a host."""
        self.verify_init()
        self.stash()
        self.debug("Setting required services")
        for dbservice in self.required_services:
            self.find_service_instances(dbservice)
        self.check_errors()
        for dbservice in self.required_services:
            self.choose_cluster_aligned(dbservice)
            self.choose_past_use(dbservice)
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
        if instance:
            self.debug("Setting service %s instance %s",
                       service.name, instance.name)
            self.staging_services[service] = [instance]
        else:
            self.debug("Setting service %s with auto-bind", service.name)
            self.staging_services[service] = None
            self.find_service_instances(service)
        self.check_errors()
        self.choose_cluster_aligned(service)
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
                       (self.description, cfg_path.relative_path))
            self.check_errors()
        self.stash_services()
        self.apply_changes()
        self.check_errors()

    def find_service_instances(self, dbservice):
        """This finds the "closest" service instances, based on the
        known maps."""
        locations = [self.location]
        while (locations[-1].parent is not None and
               locations[-1].parent != locations[-1]):
            locations.append(locations[-1].parent)
        for service_map in [PersonalityServiceMap, ServiceMap]:
            for location in locations:
                if service_map == PersonalityServiceMap:
                    self.debug("Checking personality %s %s service %s maps "
                               "for %s %s",
                               self.archetype.name,
                               self.personality.name,
                               dbservice.name,
                               location.location_type.capitalize(),
                               location.name)
                    q = self.session.query(service_map)
                    q = q.filter_by(personality=self.personality)
                else:
                    self.debug("Checking service %s maps for %s %s",
                               dbservice.name,
                               location.location_type.capitalize(),
                               location.name)
                    q = self.session.query(service_map)
                q = q.filter_by(location=location)
                q = q.join('service_instance').filter_by(service=dbservice)
                maps = q.all()
                instances = [map.service_instance for map in maps]
                if len(instances) >= 1:
                    for instance in instances:
                        self.debug("Found service %s instance %s in the maps.",
                                   instance.service.name, instance.name)
                    self.staging_services[dbservice] = instances
                    return
        self.error("Could not find a relevant service map for service %s "
                   "on %s", dbservice.name, self.description)

    def check_errors(self):
        if self.errors:
            if self.is_debug_enabled:
                raise ArgumentError("\n".join(self.debug_info))
            raise ArgumentError("\n".join(self.messages + self.errors))

    def choose_cluster_aligned(self, dbservice):
        # Only implemented for hosts.
        pass

    def choose_past_use(self, dbservice):
        """If more than one service instance was found in the maps,
        this method checks to see if we can reduce the list to a single
        choice by checking to see if any of the instances was already in use.

        """
        if len(self.staging_services[dbservice]) > 1 and \
           self.original_service_instances.get(dbservice, None) and \
           self.original_service_instances[dbservice] in \
           self.staging_services[dbservice]:
            self.debug("Chose service %s instance %s because of past use.",
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
            for sis in instances[0].servers:
                if self.servers.get(sis.system, None):
                    self.servers[sis.system] += 1
                else:
                    self.servers[sis.system] = 1

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
            self.debug("Checking service %s instance %s servers %s" %
                       (instance.service.name, instance.name,
                        [sis.system.fqdn for sis in instance.servers]))
            for sis in instance.servers:
                if self.servers.get(sis.system, None):
                    common_servers.append(sis.system)
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
                    self.debug("Discounted service %s instance %s due to "
                               "server affinity (stickiness).",
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
                    self.debug("Discounted service %s instance %s due to "
                               "load.", instance.service.name, instance.name)
            self.staging_services[dbservice] = least_loaded

    def choose_random(self, dbservice):
        """Pick a service instance randomly."""
        self.staging_services[dbservice] = [
            choice(self.staging_services[dbservice])]
        self.debug("Randomly chose service %s instance %s "
                   "from remaining choices.",
                   dbservice.name, self.staging_services[dbservice][0].name)

    def finalize_service_instances(self):
        """Fill out the list of chosen services."""
        for (service, instances) in self.staging_services.items():
            if len(instances) < 1:
                self.error("Internal Error: Attempt to finalize on "
                           "service %s without any candidates." %
                           service.name)
                continue
            if len(instances) > 1:
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
            plenary = PlenaryServiceInstanceServer(instance.service, instance)
            plenary.stash()
            self.stashed.append(plenary)

    def flush_changes(self):
        self.session.flush()
        self.session.refresh(self.dbobj)

    def write_plenary_templates(self, locked=False):
        try:
            if not locked:
                compileLock()
            for instances in [self.instances_bound, self.instances_unbound]:
                for instance in instances:
                    plenary = PlenaryServiceInstanceServer(instance.service,
                                                           instance)
                    plenary.write(locked=True)
            self.write_additional_templates(locked=True)
        finally:
            if not locked:
                compileRelease()

    def write_additional_templates(self, locked=False):
        pass

    def prestash_primary(self, plenary):
        self.stashed.append(plenary)

    def stash(self):
        pass

    def restore_stash(self):
        for plenary in self.stashed:
            plenary.restore_stash()


class HostChooser(Chooser):
    """Choose services for a host."""

    def __init__(self, dbobj, *args, **kwargs):
        """Provide initialization specific for host bindings."""
        if not isinstance(dbobj, Host):
            raise InternalError("HostChooser can only choose services for "
                                "hosts, got %r (%s)" % (dbobj, type(dbobj)))
        self.dbhost = dbobj
        Chooser.__init__(self, dbobj, *args, **kwargs)
        self.location = self.dbhost.location
        self.archetype = self.dbhost.archetype
        self.personality = self.dbhost.personality
        self.required_services = set()
        """Stores interim service instance lists."""
        for item in self.archetype.service_list:
            self.required_services.add(item.service)
        for item in self.personality.service_list:
            self.required_services.add(item.service)
        self.dbservice_tld = Tld.get_unique(self.session, 'service')
        if not self.dbservice_tld:
            raise InternalError("No config path TLDs named 'service'.")
        q = self.session.query(BuildItem).filter_by(host=self.dbhost)
        q = q.join('cfg_path').filter_by(tld=self.dbservice_tld)
        self.original_service_build_items = q.all()
        """Cache of the build_items related to services."""
        self.original_service_instances = {}
        """Cache of any already bound services (keys) and the instance
        that was bound (values).
        """
        for dbbi in self.original_service_build_items:
            if not dbbi.cfg_path.svc_inst:
                self.error("Internal Error: %s bound to template %s "
                           "which is missing a service instance aqdb entry." %
                           (self.description, dbbi.cfg_path))
                continue
            self.original_service_instances[dbbi.cfg_path.svc_inst.service] = \
                    dbbi.cfg_path.svc_inst
            self.debug("%s original binding: %s",
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
        return "host %s" % self.dbhost.fqdn

    def choose_cluster_aligned(self, dbservice):
        if dbservice not in self.cluster_aligned_services:
            return
        if not self.cluster_aligned_services[dbservice]:
            self.error("No instance set for %s cluster %s aligned service %s."
                       "  Please run `make cluster --cluster %s` to resolve.",
                       self.dbhost.cluster.cluster_type,
                       self.dbhost.cluster.name,
                       dbservice.name,
                       self.dbhost.cluster.name)
            return
        # FIXME: Is this check necessary and/or desireable?
        if self.cluster_aligned_services[dbservice] not in \
           self.staging_services[dbservice]:
            self.debug("The %s cluster %s is set to use service %s instance "
                       "%s, but that instance is not in a service map for %s.",
                       self.dbhost.cluster.cluster_type,
                       self.dbhost.cluster.name,
                       dbservice.name,
                       self.cluster_aligned_services[dbservice].name,
                       self.dbhost.fqdn)
            return
        self.debug("Chose service %s instance %s because it is cluster "
                   "aligned.", dbservice.name,
                   self.cluster_aligned_services[dbservice].name)
        self.staging_services[dbservice] = [
            self.cluster_aligned_services[dbservice]]
        return

    def apply_changes(self):
        """Update the host object with pending changes."""
        # Reserve 0 for os
        max_position = 0
        for bi in self.dbhost.templates:
            if bi.position > max_position:
                max_position = bi.position
        for instance in self.instances_bound:
            self.info("%s adding binding for service %s instance %s",
                       self.description,
                       instance.service.name, instance.name)
            if self.original_service_instances.get(instance.service, None):
                previous = None
                for bi in self.original_service_build_items:
                    if bi.cfg_path.svc_inst and \
                       bi.cfg_path.svc_inst.service == instance.service:
                        previous = bi
                        break
                if previous:
                    previous.cfg_path = instance.cfg_path
                else:
                    self.error("Internal Error: Error in alogorithm to find "
                               "previous binding for %s %s" %
                               (instance.service.name, instance.name))
                continue
            max_position += 1
            bi = BuildItem(host=self.dbhost, cfg_path=instance.cfg_path,
                           position=max_position)
            self.dbhost.templates.append(bi)
        for instance in self.instances_unbound:
            self.info("%s removing binding for service %s instance %s",
                       self.description,
                       instance.service.name, instance.name)
            if self.chosen_services.get(instance.service, None):
                # We have a replacement, no need to remove BuildItem
                continue
            found_instance = False
            for bi in self.original_service_build_items:
                if bi.cfg_path.svc_inst == instance:
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
            #if self.dbhost.templates and \
            #   self.dbhost.templates[0].cfg_path.tld.type == 'os':
            #    self.dbhost.templates._reorder()
            self.session.add(self.dbhost)

    def stash(self):
        if not self.stashed:
            plenary_host = PlenaryHost(self.dbhost)
            plenary_host.stash()
            self.stashed.append(plenary_host)

    def write_additional_templates(self, locked=False):
        plenary = PlenaryHost(self.dbhost)
        try:
            plenary.write(locked=locked)
        except IncompleteError, e:
            pass


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
            self.debug("%s original binding: %s",
                       self.description, si.cfg_path)

    def generate_description(self):
        return "%s cluster %s" % (self.dbcluster.cluster_type,
                                  self.dbcluster.name)

    def apply_changes(self):
        """Update the cluster object with pending changes."""
        for instance in self.instances_unbound:
            self.info("%s removing binding for service %s instance %s",
                       self.description,
                       instance.service.name, instance.name)
            dbcs = ClusterServiceBinding.get_unique(
                cluster_id=self.dbcluster.id,
                service_instance_id=instance.id)
            if dbcs:
                self.session.delete(dbcs)
            else:
                self.error("Internal Error: Could not unbind "
                           "service %s instance %s" %
                           (instance.service.name, instance.name))
        for instance in self.instances_bound:
            self.info("%s adding binding for service %s instance %s",
                       self.description,
                       instance.service.name, instance.name)
            dbcs = ClusterServiceBinding(cluster=self.dbcluster,
                                         service_instance=instance)
            self.session.add(dbcs)
            self.flush_changes()
            for h in self.dbcluster.hosts:
                host_plenary = PlenaryHost(h)
                host_plenary.stash()
                self.stashed.append(host_plenary)
                host_chooser = Chooser(dbhost, required_only=False,
                                       debug=self.is_debug_enabled)
                host_chooser.set_single(instance.service, instance, force=True)
                host_chooser.flush_changes()
                # FIXME: Merge host_chooser debug_info with self.debug_info?
                # Note, host plenary will be written later.
        if self.instances_bound or self.instances_unbound:
            self.session.add(self.dbcluster)

    def stash(self):
        if not self.stashed:
            plenary_cluster = PlenaryCluster(self.dbcluster)
            plenary_cluster.stash()
            self.stashed.append(plenary_cluster)

    def write_additional_templates(self, locked=False):
        plenary = PlenaryCluster(self.dbcluster)
        plenary.write(locked=locked)
        if self.instances_bound:
            for h in self.dbcluster.hosts:
                plenary = PlenaryHost(self.dbhost)
                try:
                    plenary.write(locked=locked)
                except IncompleteError, e:
                    pass


