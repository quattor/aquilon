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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Tld, BuildItem, ServiceMap,
                                PersonalityServiceMap, ClusterServiceBinding)
from aquilon.server.templates.service import PlenaryServiceInstanceServer


log = logging.getLogger('aquilon.server.services')

class Chooser(object):
    """Choose services for a host."""

    def __init__(self, dbhost, required_only=False, debug=False):
        """To clear out bindings that are not required, pass in
        required_only=True.

        A compile lock should be held before creating this object.

        If the debug flag is set to True, debug output will be
        gathered in an array for later use by the calling code.

        Several staging areas and caches are set up within this object.
        The general flow is that potential service instance choices
        are kept in staging_services (dictionary of service to list of
        service instances) and finalized into chosen_services (dictionary
        of service to single service instance).

        The original state of the host is held in the caches
        original_service_build_items (list of build items, but only
        services) and original_service_instances (dictionary of
        service to single service instance).

        The instances_bound and instances_unbound lists are populated
        after chosen_services with the differences between chosen_services
        and original_service_instances.

        """
        self.dbhost = dbhost
        self.is_debug_enabled = debug
        self.debug_info = []
        """Store debug information."""
        self.debug("Creating service Chooser for %s", self.dbhost.fqdn)
        self.required_only = required_only
        self.session = object_session(self.dbhost)
        q = self.session.query(Tld).filter_by(type='service')
        self.dbservice_tld = q.one()
        self.required_services = set()
        """Stores interim service instance lists."""
        for item in self.dbhost.archetype.service_list:
            self.required_services.add(item.service)
        for item in self.dbhost.personality.service_list:
            self.required_services.add(item.service)
        self.cluster_aligned_services = {}
        if self.dbhost.cluster:
            for si in self.dbhost.cluster.service_bindings:
                self.cluster_aligned_services[si.service] = si
            q = session.query(ClusterAlignedService)
            q = q.filter_by(cluster_type=self.dbhost.cluster.cluster_type)
            for item in q.all():
                if item.service not in self.cluster_aligned_services:
                    self.cluster_aligned_services[item.service] = None
                self.required_services.add(item.service)
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
        self.cluster_instances_bound = set()
        """Set of newly bound instances for cluster aligned services."""
        self.cluster_instances_unbound = set()
        """Set of instances unbound as cluster aligned services."""
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
                self.error("Internal Error: Host %s bound to template %s "
                           "which is missing a service instance aqdb entry." %
                           (dbhost.fqdn, dbbi.cfg_path))
                continue
            self.original_service_instances[dbbi.cfg_path.svc_inst.service] = \
                    dbbi.cfg_path.svc_inst
            self.debug("%s original binding: %s",
                       self.dbhost.fqdn, dbbi.cfg_path)
        self.chosen_services = {}
        """Track the chosen services."""
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
        self.apply_changes()
        self.check_errors()

    def set_single(self, service, instance=None, force=False):
        """Use this to update a single service.

        If planning to use this method, construct the Chooser with
        required_only=False.  If required_only is True, all other
        bindings will be cleared.

        """
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
        # In theory don't always need the loop above, either.
        self.count_servers()
        self.reduce_service_instances(service)
        self.finalize_service_instances()
        self.analyze_changes()
        if not force and self.instances_bound and self.instances_unbound:
            cfg_path = list(self.instances_unbound)[0].cfg_path
            self.error("Host %s is already bound to %s, use unbind "
                       "to clear first or rebind to force." %
                       (self.dbhost.fqdn, cfg_path.relative_path))
            self.check_errors()
        self.apply_changes()
        self.check_errors()

    def find_service_instances(self, dbservice):
        """This finds the "closest" service instances, based on the
        known maps."""
        if dbservice in self.cluster_aligned_services:
            locations = [self.dbhost.cluster.location_constraint]
        else:
            locations = [self.dbhost.location]
        while (locations[-1].parent is not None and
               locations[-1].parent != locations[-1]):
            locations.append(locations[-1].parent)
        for service_map in [PersonalityServiceMap, ServiceMap]:
            for location in locations:
                if service_map == PersonalityServiceMap:
                    self.debug("Checking personality %s %s service %s maps "
                               "for %s %s",
                               self.dbhost.archetype.name,
                               self.dbhost.personality.name,
                               dbservice.name,
                               location.location_type.capitalize(),
                               location.name)
                    q = self.session.query(service_map)
                    q = q.filter_by(personality=self.dbhost.personality)
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
                   "on host %s", dbservice.name, self.dbhost.fqdn)

    def check_errors(self):
        if self.errors:
            if self.is_debug_enabled:
                raise ArgumentError("\n".join(self.debug_info))
            raise ArgumentError("\n".join(self.messages + self.errors))

    def choose_cluster_aligned(self, dbservice):
        if dbservice not in self.cluster_aligned_services:
            return
        if not self.cluster_aligned_services[dbservice]:
            self.debug("No instance set for %s cluster %s service %s",
                       self.dbhost.cluster.cluster_type,
                       self.dbhost.cluster.name,
                       dbservice.name)
            return
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
        for (service, instance) in self.cluster_aligned_services.items():
            if not instance or instance != self.chosen_services[service]:
                self.cluster_instances_bound.add(self.chosen_services[service])
            if instance != self.chosen_services[service]:
                self.cluster_instances_unbound.add(instance)

    def apply_changes(self):
        """Update the host object with pending changes."""
        # Reserve 0 for os
        max_position = 0
        for bi in self.dbhost.templates:
            if bi.position > max_position:
                max_position = bi.position
        for instance in self.instances_bound:
            self.info("%s adding binding for service %s instance %s",
                       self.dbhost.fqdn,
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
                       self.dbhost.fqdn,
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
        for instance in self.cluster_instances_unbound:
            dbcs = ClusterServiceBinding.get_unique(
                cluster_id=self.dbhost.cluster.id,
                service_instance_id=instance.id)
            if dbcs:
                self.session.remove(dbcs)
        for instance in self.cluster_instances_bound:
            # XXX: New binding should propogate out to other cluster
            # members but currently does not.
            dbcs = ClusterServiceBinding(cluster=self.dbhost.cluster,
                                         service_instance=instance)
            self.session.add(dbcs)

    def flush_changes(self):
        self.session.flush()
        self.session.refresh(self.dbhost)

    def write_plenary_templates(self, locked=False):
        for instances in [self.instances_bound, self.instances_unbound]:
            for instance in instances:
                plenary_info = PlenaryServiceInstanceServer(instance.service,
                                                            instance)
                plenary_info.write(locked=locked)
        # FIXME: If a service instance has been newly set for a cluster
        # aligned service, do we need to write out any plenary files
        # for this host's cluster?
        if self.cluster_instances_bound:
            pass


