# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016,2017  Contributor
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
""" Helper functions for change management """

import collections
import json
import shlex

from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality, HardwareEntity,
                                PersonalityStage, InterfaceFeature, Domain, Sandbox, Machine,
                                HardwareFeature, HostFeature, ServiceInstance, NetworkDevice,
                                OperatingSystem, ComputeCluster, StorageCluster, Network,
                                EsxCluster, HostClusterMember, HostEnvironment, AddressAssignment,
                                MetaCluster, ClusterLifecycle, HostLifecycle, Interface,
                                HostResource, Resource, ServiceAddress, ARecord, ClusterResource,
                                ResourceGroup, BundleResource, Chassis, ChassisSlot, Location, Rack,
                                Share, Alias, NetworkCompartment, DnsEnvironment, NetworkEnvironment,
                                Fqdn, ARecord, ReservedName, AddressAlias, DnsDomain, DnsRecord, NsRecord,
                                SrvRecord, DynamicStub)
from aquilon.aqdb.model.host_environment import Development, UAT, QA, Legacy, Production, Infra
from aquilon.config import Config
from aquilon.exceptions_ import AuthorizationException, InternalError
from aquilon.worker.dbwrappers.user_principal import get_or_create_user_principal
from aquilon.worker.processes import run_command
from sqlalchemy.orm import contains_eager, load_only, aliased
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.query import Query


class ChangeManagement(object):
    """
    Class calculate impacted environments with number objects in them
    for impacted target
    Command to be called for individual targets:
    host, cluster, feature, service instance, personality stage,
    os type, arch type, domain, host environment
    Calculate target grn (eonid) - TBD
    Prepare input for aqd_checkedm
    Call aqd_checkedm
    """
    config = Config()
    check_enabled = False
    extra_options = ""
    handlers = {}
    lifecycle_status_edm_check = ['ready']  # Crash and burn: 'build', 'rebuild',
    # 'decommissioned', 'blind', 'install', 'reinstall', 'almostready', 'failed'

    def __init__(self, session, user, justification, reason, logger, command):
        self.command = command
        self.justification = justification
        self.reason = reason
        self.logger = logger

        self.dict_of_impacted_envs = {}
        self.eonid = 6980  # to be calculated for each target
        self.enforce_validation = False

        if self.config.has_option("change_management", "enable"):
            self.check_enabled = self.config.getboolean("change_management", "enable")
        if self.config.has_option("change_management", "extra_options"):
            self.extra_options = self.config.get("change_management", "extra_options")

        dbuser = get_or_create_user_principal(session, user, commitoncreate=True)
        self.username = dbuser.name
        self.role_name = dbuser.role.name

    def consider(self, target_obj, enforce_validation=False):
        """
        Entry point validation method, chooses right validation method based on the object class
        and self.handlers dict
        Args:
            target_obj: queryset or single db model object
            enforce_validation: True or False
        Returns: None or raises InternalError/AuthorizationException
        """
        if enforce_validation:
            self.enforce_validation = enforce_validation
        if not self.check_enabled:
            self.logger.debug('Change management is disabled. Exiting validate.')
            return
        self.logger.debug('Determine if the input object is a queryset or a single object')
        if not target_obj:
            self.logger.debug('Given objects is None. Nothing to validate.')
            return
        # If given object is query use it for validation
        # to optimize validation of large amount of data
        if isinstance(target_obj, Query):
            if target_obj.count() == 0:
                self.logger.debug('No impacted targets exiting')
                return
            self._call_handler_method(target_obj.first(), queryset=target_obj)
        # If given Query is evaluated with .all() it is an instance of collections.Iterable
        # then validate each item in the list separatelly
        elif isinstance(target_obj, collections.Iterable):
            for obj in target_obj:
                self._call_handler_method(obj)
        else:
            self._call_handler_method(target_obj)
        self.logger.debug('Call aqd_checkedm with metadata')

    def _call_handler_method(self, obj, queryset=None):
        env_calculate_method = self.handlers.get(obj.__class__, None)
        if not env_calculate_method:
            raise InternalError('Change management calculate impact fail. Target class unknown.')
        self.logger.debug('Calculate impacted environments and target status')
        if queryset:
            env_calculate_method(self, queryset)
        else:
            env_calculate_method(self, obj)

    def validate(self):
        """
        Method calls adq_checkedm cmd tool with target resources metadata
        to calculate if change management validation is required.
        If required, justification validation will happen. If EDM calls
        enabled, the ticket will be checked in EDM.
        Returns: None or raises AuthorizationException
        """
        if not self.check_enabled:
            self.logger.debug('Change management is disabled. Exiting validate.')
            return

        # Clean final impacted env list
        self.logger.debug('Prepare impacted envs to call EDM')
        for env, build_status_list in self.dict_of_impacted_envs.items():
            self.dict_of_impacted_envs[env] = list(set(build_status_list))
        # Prepare aqd_checkedm input dict
        cmd = ["aqd_checkedm"] + shlex.split(self.extra_options)
        metadata = {"ticket": self.justification,
                    "reason": self.reason,
                    "requestor": self.username,
                    "requestor_role": self.role_name,
                    "command": self.command,
                    "impacted_envs": self.dict_of_impacted_envs,
                    "eonid": self.eonid,
                    "enforce_validation": self.enforce_validation,
                    }
        cmd.extend(["--metadata", json.dumps(metadata)])
        try:
            out = run_command(cmd)
            out_dict = json.loads(out)
        except Exception as err:
            self.logger.info("Change Management validation failed. Reason: {}".format(str(err)))
            raise InternalError(str(err))

        self.logger.info("Change Management validation finished. Status: {}. {}".format(out_dict.get("Status"), out_dict.get("Reason")))
        if out_dict.get("Status") == 'Permitted':
            self.logger.client_info("Approval Warning: {}".format(out_dict.get("Reason")))
        elif out_dict.get("Status") != 'Approved':
            raise AuthorizationException(out_dict.get("Reason"))

    def validate_default(self, obj):
        pass

    def validate_branch(self, obj):
        """
        Method to be used when we do not need calculate impacted environment
        Used with enforce_validation for some models, i.e. Domain, Sandbox
        If enforce_validation is set, do not perform extra database queries
        to get hosts and clusters impacted
        Returns:

        """
        if obj.requires_change_manager:
            self.enforce_validation = True

    def validate_prod_personality(self, personality_stage):
        session = object_session(personality_stage)
        if personality_stage.personality.is_cluster:
            q = session.query(Cluster)
            q = q.filter_by(personality_stage=personality_stage)
            q = q.join(ClusterLifecycle)
        else:
            q = session.query(Host)
            q = q.filter_by(personality_stage=personality_stage)
            q = q.join(HostLifecycle)
        q = q.options(contains_eager('status'))
        q = q.join(PersonalityStage, Personality, HostEnvironment)
        q = q.options(contains_eager('personality_stage.personality.host_environment'))

        if isinstance(q.first(), Cluster):
            for cluster in q.all():
                self.validate_cluster(cluster)
        else:
            for host in q.all():
                self.validate_host(host)

    def validate_cluster(self, cluster):
        """
        Validate impacted cluster and its hosts so that if
        cluster env is infra but hosts are prod/ready CM would be enabled
        Args:
            cluster: single Cluster
        Returns: None
        """
        # Validate only the impacted cluster
        self.dict_of_impacted_envs.setdefault(
            cluster.personality_stage.personality.host_environment.name, []).append(cluster.status.name)
        # Also validate cluster hosts
        for host in cluster.hosts:
            self.validate_host(host)
        if hasattr(cluster, 'members'):
            for cluster_member in cluster.members:
                self.validate_cluster(cluster_member)
        # To do: Do we want to check if cluster is assigned
        # to metacluster and if yes validate metacluster and its clusters/hosts?

    def validate_host(self, host):
        """
        Validate given single host
        Args:
            host: a single host
        Returns: None
        """
        self.dict_of_impacted_envs.setdefault(
            host.personality_stage.personality.host_environment.name, []).append(host.status.name)

    def validate_hardware_entity(self, hwentities_or_hwentity):
        """
        Validate given single hardware entities query or a single object
        Args:
            hwentity: queryset or single subclass of hardware entity
        Returns: None
        """
        # Check if there cannot be a case when one machine can
        # have multiple hosts assigned - vms seems to be handled separately?
        # Chassis/ChassisSlots?
        if isinstance(hwentities_or_hwentity, HardwareEntity):
            if hwentities_or_hwentity.host:
                self.validate_host(hwentities_or_hwentity.host)
        else:
            hwentities_or_hwentity = hwentities_or_hwentity.join(Host).options(contains_eager('host'))
            for hwentity in hwentities_or_hwentity.all():
                self.validate_host(hwentity.host)

    def validate_location(self, location):
        session = object_session(location)
        q = session.query(Host).join(HardwareEntity,
                                     Host.hardware_entity_id == HardwareEntity.id).\
            join(Location, HardwareEntity.location_id == Location.id).filter(Location.id == location.id)

        for host in q.all():
            self.validate_host(host)

    def validate_prod_network(self, network_or_networks):
        """
        Validate queryset or single network object
        Args:
            networkor_networks: queryset or single network object
        Returns: None
        """
        CR = aliased(ClusterResource)
        HR = aliased(HostResource)
        S = aliased(ServiceAddress)
        RG = aliased(ResourceGroup)
        BR = aliased(BundleResource)

        if isinstance(network_or_networks, Network):
            session = object_session(network_or_networks)
            # Filter Service addresses mapped to the clusters directly
            q2 = session.query(Cluster).join(CR).join(Resource).\
                join(ServiceAddress).join(ARecord).join(Network).filter(Network.id==network_or_networks.id)

            # Filter Service addresses mapped to the cluster via resourcegroups
            q5 = session.query(Cluster).join(CR)
            q5 = q5.outerjoin((RG, RG.holder_id == CR.id),
                              (BR, BR.resourcegroup_id == RG.id),
                              (S, S.holder_id == BR.id))
            q5 = q5.join(ARecord).join(Network).filter(Network.id==network_or_networks.id)

            # Filter IP Addresses assigned to the hosts
            q3 = session.query(Host).join(HardwareEntity).join(Interface, aliased=True). \
                join(AddressAssignment, from_joinpoint=True).join(Network). \
                filter(Network.id==network_or_networks.id)
            # Filter Service addresses mapped to the hosts directly
            q4 = session.query(Host).join(HardwareEntity).join(HostResource).join(Resource).\
                join(ServiceAddress).join(ARecord).join(Network).filter(Network.id==network_or_networks.id)

            # Filter Service addresses mapped to the host via resourcegroups
            q6 = session.query(Host).join(HR)
            q6 = q6.outerjoin((RG, RG.holder_id == HR.id),
                              (BR, BR.resourcegroup_id == RG.id),
                              (S, S.holder_id == BR.id))
            q6 = q6.join(ARecord).join(Network).filter(Network.id==network_or_networks.id)

        else:
            session = object_session(network_or_networks.first())
            network_sub_q = network_or_networks.options(load_only("id")).subquery()
            # Filter Service addresses mapped to the clusters directly
            q2 = session.query(Cluster).join(ClusterResource).join(Resource).\
                join(ServiceAddress).join(ARecord).join(Network).filter(Network.id.in_(network_sub_q))

            # Filter Service addresses mapped to the cluster via resourcegroups
            q5 = session.query(Cluster).join(CR)
            q5 = q5.outerjoin((RG, RG.holder_id == CR.id),
                            (BR, BR.resourcegroup_id == RG.id),
                            (S, S.holder_id == BR.id))
            q5 = q5.join(ARecord).join(Network).filter(Network.id.in_(network_sub_q))

            # Filter IP Addresses assigned to the hosts
            q3 = session.query(Host).join(HardwareEntity).join(Interface, aliased=True).\
                join(AddressAssignment, from_joinpoint=True).join(Network).\
                filter(Network.id.in_(network_sub_q))
            # Filter Service addresses mapped to the hosts directly
            q4 = session.query(Host).join(HardwareEntity).join(HostResource).join(Resource).\
                join(ServiceAddress).join(ARecord).join(Network).filter(Network.id.in_(network_sub_q))

            # Filter Service addresses mapped to the host via resourcegroups
            q6 = session.query(Host).join(HR)
            q6 = q6.outerjoin((RG, RG.holder_id == HR.id),
                              (BR, BR.resourcegroup_id == RG.id),
                              (S, S.holder_id == BR.id))
            q6 = q6.join(ARecord).join(Network).filter(Network.id.in_(network_sub_q))

        # Validate clusters
        for q in [q2, q5]:
            q = q.reset_joinpoint()
            q = q.join(ClusterLifecycle).options(contains_eager('status'))
            q = q.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for cluster in q.all():
                self.validate_cluster(cluster)

        # Validate hosts
        for q in [q3, q4, q6]:
            q = q.reset_joinpoint()
            q = q.join(HostLifecycle).options(contains_eager('status'))
            q = q.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for host in q.all():
                self.validate_host(host)

    def validate_fqdn(self, dbfqdn):
        # Check full depth of fqdn aliases or address_alias!
        def dig_to_real_target(dbfqdn):
            fqdns_to_test = [dbfqdn]
            fqdns_tested = list()
            final_target = dbfqdn
            while fqdns_to_test:
                to_test_now = []
                for db_fqdn in fqdns_to_test:
                    to_test_now.extend(db_fqdn.dns_records)
                    fqdns_tested.append(db_fqdn)
                fqdns_to_test = []
                for rec in to_test_now:
                    if rec in fqdns_tested:
                        raise Exception("There might be a loop!!! Failing fast instead.")
                    if isinstance(rec, AddressAlias):
                        fqdns_to_test.append(rec.target)
                    elif isinstance(rec, Alias):
                        fqdns_to_test.append(rec.target)
                    else:
                        final_target = rec.fqdn
                    fqdns_to_test = list(set(fqdns_to_test))
            return final_target

        fqdn = dig_to_real_target(dbfqdn)

        CR = aliased(ClusterResource)
        HR = aliased(HostResource)
        S = aliased(ServiceAddress)
        RG = aliased(ResourceGroup)
        BR = aliased(BundleResource)

        session = object_session(fqdn)
        ip_subquery = session.query(ARecord).filter(ARecord.fqdn_id == fqdn.id)
        ip_subquery = [i.ip for i in ip_subquery]

        # Filter Service addresses mapped to the clusters directly
        q2 = session.query(Cluster).join(CR).join(Resource). \
            join(ServiceAddress).join(ARecord).filter(ARecord.fqdn_id == fqdn.id)

        # Filter Service addresses mapped to the cluster via resourcegroups
        q5 = session.query(Cluster).join(CR)
        q5 = q5.outerjoin((RG, RG.holder_id == CR.id),
                          (BR, BR.resourcegroup_id == RG.id),
                          (S, S.holder_id == BR.id))
        q5 = q5.join(ARecord).filter(ARecord.fqdn_id == fqdn.id)

        # Filter IP Addresses assigned to the hosts
        q3 = session.query(Host).join(HardwareEntity).join(Interface, aliased=True). \
            join(AddressAssignment).filter(AddressAssignment.ip.in_(ip_subquery))

        # Filter Service addresses mapped to the hosts directly
        q4 = session.query(Host).join(HardwareEntity).join(HostResource).join(Resource). \
            join(ServiceAddress).join(ARecord).filter(ARecord.fqdn_id == fqdn.id)

        # Filter Service addresses mapped to the host via resourcegroups
        q6 = session.query(Host).join(HR)
        q6 = q6.outerjoin((RG, RG.holder_id == HR.id),
                          (BR, BR.resourcegroup_id == RG.id),
                          (S, S.holder_id == BR.id))
        q6 = q6.join(ARecord).filter(ARecord.fqdn_id == fqdn.id)

        # Validate clusters
        for q in [q2, q5]:
            q = q.reset_joinpoint()
            q = q.join(ClusterLifecycle).options(contains_eager('status'))
            q = q.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for cluster in q.all():
                self.validate_cluster(cluster)

        # Validate hosts
        for q in [q3, q4, q6]:

            q = q.reset_joinpoint()
            q = q.join(HostLifecycle).options(contains_eager('status'))
            q = q.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for host in q.all():
                self.validate_host(host)

    def validate_chassis(self, chassis):
        """
        Validate if given chassis object has hosts in slots
        Args:
            chassis: single chassis object
        Returns: None
        """
        for slot in chassis.slots:
            if slot.machine.host:
                self.validate_host(slot.machine.host)

    def validate_resource_holder(self, resource_holder):
        session = object_session(resource_holder)
        CR = aliased(ClusterResource)
        HR = aliased(HostResource)
        RG = aliased(ResourceGroup)
        BR = aliased(BundleResource)
        q = None
        q2 = None

        if isinstance(resource_holder, BundleResource):
            q = session.query(Cluster).join(CR)
            q = q.outerjoin((RG, RG.holder_id == CR.id), (BR, BR.resourcegroup_id == RG.id))
            q = q.filter(BR.id == resource_holder.id)

            q2 = session.query(Host).join(HR)
            q2 = q2.outerjoin((RG, RG.holder_id == HR.id), (BR, BR.resourcegroup_id == RG.id))
            q2 = q2.filter(BR.id == resource_holder.id)

        elif isinstance(resource_holder, ClusterResource):
            q = session.query(Cluster).join(CR)
            q = q.filter(CR.id == resource_holder.id)

        elif isinstance(resource_holder, HostResource):
            q2 = session.query(Host).join(HR)
            q2 = q2.filter(HR.id == resource_holder.id)

        # Validate Clusters
        if q:
            q = q.reset_joinpoint()
            q = q.join(ClusterLifecycle).options(contains_eager('status'))
            q = q.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for cluster in q.all():
                self.validate_cluster(cluster)

        # Validate hosts
        if q2:
            q2 = q2.reset_joinpoint()
            q2 = q2.join(HostLifecycle).options(contains_eager('status'))
            q2 = q2.join(PersonalityStage,Personality).join(HostEnvironment).options(contains_eager('personality_stage.personality.host_environment'))
            for host in q2.all():
                self.validate_host(host)

    def validate_host_environment(self, host_environment):
        if host_environment.name == 'prod':
            self.enforce_validation = True

    def validate_prod_archetype(self, archtype):
        session = object_session(archtype)
        if archtype.cluster_type:
            q = session.query(Cluster)
            q = q.join(ClusterLifecycle)
        else:
            q = session.query(Host)
            q = q.join(HostLifecycle)
        q = q.options(contains_eager('status'))
        q = q.join(PersonalityStage, Personality)
        q = q.filter_by(archetype=archtype)
        q = q.join(HostEnvironment)
        q = q.options(contains_eager('personality_stage.personality.host_environment'))

        if isinstance(q.first(), Cluster):
            for cluster in q.all():
                self.validate_cluster(cluster)
        else:
            for host in q.all():
                self.validate_host(host)

    def validate_prod_os(self, ostype):
        session = object_session(ostype)

        q = session.query(Host)
        q = q.filter_by(operating_system=ostype)
        q = q.join(HostLifecycle)
        q = q.options(contains_eager('status'))
        q = q.join(PersonalityStage, Personality, HostEnvironment)
        q = q.options(contains_eager('personality_stage.personality.host_environment'))

        for host in q.all():
            self.validate_host(host)

    def validate_prod_service_instance(self, service_instance):
        session = object_session(service_instance)

        q1 = session.query(Cluster)
        q1 = q1.filter(Cluster.services_used.contains(service_instance))
        q1 = q1.join(ClusterLifecycle)
        q1 = q1.options(contains_eager('status'))
        q1 = q1.join(PersonalityStage, Personality, HostEnvironment)
        q1 = q1.options(contains_eager('personality_stage.personality.host_environment'))

        for cluster in q1.all():
            self.validate_cluster(cluster)

        q2 = session.query(Host)
        q2 = q2.filter(Host.services_used.contains(service_instance))
        q2 = q2.join(HostLifecycle)
        q2 = q2.options(contains_eager('status'))
        q2 = q2.join(PersonalityStage, Personality, HostEnvironment)
        q2 = q2.options(contains_eager('personality_stage.personality.host_environment'))

        for host in q2.all():
            self.validate_host(host)

    def validate_prod_feature(self, feature):
        session = object_session(feature)

        q1 = session.query(Cluster)
        q1 = q1.join(ClusterLifecycle)
        q1 = q1.options(contains_eager('status'))
        q1 = q1.join(PersonalityStage)
        q1 = q1.join(PersonalityStage.features)
        q1 = q1.filter_by(feature=feature)
        q1 = q1.join(Personality, HostEnvironment)
        q1 = q1.options(contains_eager('personality_stage.personality.host_environment'))

        for cluster in q1.all():
            self.validate_cluster(cluster)

        q2 = session.query(Host)
        q2 = q2.join(PersonalityStage)
        q2 = q2.join(PersonalityStage.features)
        q2 = q2.filter_by(feature=feature)
        q2 = q2.join(Personality, HostEnvironment)
        q2 = q2.options(contains_eager('personality_stage.personality.host_environment'))

        for host in q2.all():
            self.validate_host(host)


ChangeManagement.handlers[Cluster] = ChangeManagement.validate_cluster
ChangeManagement.handlers[ComputeCluster] = ChangeManagement.validate_cluster
ChangeManagement.handlers[StorageCluster] = ChangeManagement.validate_cluster
ChangeManagement.handlers[EsxCluster] = ChangeManagement.validate_cluster
ChangeManagement.handlers[HostClusterMember] = ChangeManagement.validate_cluster
ChangeManagement.handlers[MetaCluster] = ChangeManagement.validate_cluster
ChangeManagement.handlers[PersonalityStage] = ChangeManagement.validate_prod_personality
ChangeManagement.handlers[InterfaceFeature] = ChangeManagement.validate_prod_feature
ChangeManagement.handlers[HardwareFeature] = ChangeManagement.validate_prod_feature
ChangeManagement.handlers[HostFeature] = ChangeManagement.validate_prod_feature
ChangeManagement.handlers[ServiceInstance] = ChangeManagement.validate_prod_service_instance
ChangeManagement.handlers[OperatingSystem] = ChangeManagement.validate_prod_os
ChangeManagement.handlers[Archetype] = ChangeManagement.validate_prod_archetype
ChangeManagement.handlers[Development] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[UAT] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[QA] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[Legacy] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[Production] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[Infra] = ChangeManagement.validate_host_environment
ChangeManagement.handlers[Domain] = ChangeManagement.validate_branch
ChangeManagement.handlers[Host] = ChangeManagement.validate_host
ChangeManagement.handlers[Machine] = ChangeManagement.validate_hardware_entity
# Removing this as the HardwareEntity is too general, we have validate_hardware_entity, validate_host and validate_chassis
#ChangeManagement.handlers[HardwareEntity] = ChangeManagement.validate_hardware_entity
ChangeManagement.handlers[NetworkDevice] = ChangeManagement.validate_hardware_entity
ChangeManagement.handlers[Network] = ChangeManagement.validate_prod_network
ChangeManagement.handlers[Chassis] = ChangeManagement.validate_chassis
ChangeManagement.handlers[Rack] = ChangeManagement.validate_location
ChangeManagement.handlers[BundleResource] = ChangeManagement.validate_resource_holder
ChangeManagement.handlers[ClusterResource] = ChangeManagement.validate_resource_holder
ChangeManagement.handlers[HostResource] = ChangeManagement.validate_resource_holder
ChangeManagement.handlers[Fqdn] = ChangeManagement.validate_fqdn
ChangeManagement.handlers[DnsDomain] = ChangeManagement.validate_default
ChangeManagement.handlers[DnsEnvironment] = ChangeManagement.validate_default
ChangeManagement.handlers[NetworkCompartment] = ChangeManagement.validate_default
ChangeManagement.handlers[NetworkEnvironment] = ChangeManagement.validate_default