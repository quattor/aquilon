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

import json
import shlex

from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality,
                                PersonalityStage, InterfaceFeature, Domain,
                                HardwareFeature, HostFeature, ServiceInstance,
                                OperatingSystem, ComputeCluster, StorageCluster,
                                EsxCluster, HostClusterMember, HostEnvironment,
                                MetaCluster, ClusterLifecycle, HostLifecycle)
from aquilon.aqdb.model.host_environment import Development, UAT, QA, Legacy, Production, Infra
from aquilon.config import Config
from aquilon.exceptions_ import AuthorizationException, InternalError, ProcessException
from aquilon.worker.dbwrappers.user_principal import get_user_principal
from aquilon.worker.processes import run_command
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.session import object_session


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
    success_responses = ["Permitted", "Approved"]

    def __init__(self, session, user, justification, reason, logger, command):
        self.command = command
        self.justification = justification
        self.reason = reason
        self.logger = logger

        self.dict_of_impacted_envs = {}
        self.eonid = 6980  # to be calculated for each target

        if self.config.has_option("change_management", "enable"):
            self.check_enabled = self.config.getboolean("change_management", "enable")
        if self.config.has_option("change_management", "extra_options"):
            self.extra_options = self.config.get("change_management", "extra_options")

        dbuser = get_user_principal(session, user)
        self.username = dbuser.name
        self.role_name = dbuser.role.name

    def validate(self, target_obj, enforce_validation=False):
        print('Is change management enabled?', self.check_enabled)
        if not self.check_enabled:
            return
        print('Calculate impacted environments and target status')
        env_calculate_method = self.handlers.get(target_obj.__class__, None)
        if env_calculate_method:
            env_calculate_method(self, target_obj)
            print('Prepare impacted envs to call EDM')
            for env, build_status_list in self.dict_of_impacted_envs.items():
                self.dict_of_impacted_envs[env] = list(set(build_status_list))
        else:
            raise InternalError('Change management calculate impact fail. Target class unknown.')
        print('Call aqd_checkedm with metadata')
        self.change_management_validate(enforce_validation=enforce_validation)

    def change_management_validate(self, enforce_validation):
        """
        Method calls adq_checkedm cmd tool with target resources metadata
        to calculate if change management validation is required.
        If required, justification validation will happen. If EDM calls
        enabled, the ticket will be checked in EDM.
        Args:
            enforce_validation: enforce justification validation,
            disregarding impacted environment dict

        Returns: None or raises AuthorizationException

        """
        cmd = ["aqd_checkedm"] + shlex.split(self.extra_options)
        metadata = {"ticket": self.justification,
                    "reason": self.reason,
                    "requestor": self.username,
                    "requestor_role": self.role_name,
                    "command": self.command,
                    "impacted_envs": self.dict_of_impacted_envs,
                    "eonid": self.eonid,
                    "enforce_validation": enforce_validation,
                    }
        cmd.extend(["--metadata", json.dumps(metadata)])

        try:
            out = run_command(cmd)
            out_dict = json.loads(out)
        except Exception as err:
            raise InternalError(str(err))

        if out_dict.get("Status") in self.success_responses:
            self.logger.info("Status: {}. {}".format(out_dict.get("Status"), out_dict.get("Reason")))
        else:
            raise AuthorizationException(out_dict.get("Reason"))

    def validate_default(self, obj):
        """
        Method to be used when we do not need calculate impacted environment
        Used with enforce_validation for some models, i.e. Domain
        Returns:

        """
        pass

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

        for target in q.all():
            self.dict_of_impacted_envs.setdefault(
                target.personality_stage.personality.host_environment.name, []).append(target.status.name)

    def validate_prod_cluster(self, cluster):
        # validate only cluster status, leave out hosts
        self.validate_prod_personality(cluster.personality_stage)

    def validate_host_environment(self, host_environment):
        session = object_session(host_environment)

        q1 = session.query(Cluster)
        q1 = q1.join(ClusterLifecycle)
        q1 = q1.options(contains_eager('status'))
        q1 = q1.join(PersonalityStage)
        q1 = q1.join(Personality)
        q1 = q1.filter_by(host_environment=host_environment)

        for cluster in q1.all():
            self.dict_of_impacted_envs.setdefault(
                host_environment.name, []).append(cluster.status.name)

        q2 = session.query(Host)
        q2 = q2.join(HostLifecycle)
        q2 = q2.options(contains_eager('status'))
        q2 = q2.join(PersonalityStage)
        q2 = q2.join(Personality)
        q2 = q2.filter_by(host_environment=host_environment)

        for host in q2.all():
            self.dict_of_impacted_envs.setdefault(
                host_environment.name, []).append(host.status.name)

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

        for target in q.all():
            self.dict_of_impacted_envs.setdefault(
                target.personality_stage.personality.host_environment.name, []).append(target.status.name)

    def validate_prod_os(self, ostype):
        session = object_session(ostype)

        q = session.query(Host)
        q = q.filter_by(operating_system=ostype)
        q = q.join(HostLifecycle)
        q = q.options(contains_eager('status'))
        q = q.join(PersonalityStage, Personality, HostEnvironment)
        q = q.options(contains_eager('personality_stage.personality.host_environment'))

        for target in q.all():
            self.dict_of_impacted_envs.setdefault(
                target.personality_stage.personality.host_environment.name, []).append(target.status.name)

    def validate_prod_service_instance(self, service_instance):
        session = object_session(service_instance)

        q1 = session.query(Cluster)
        q1 = q1.filter(Cluster.services_used.contains(service_instance))
        q1 = q1.join(ClusterLifecycle)
        q1 = q1.options(contains_eager('status'))
        q1 = q1.join(PersonalityStage, Personality, HostEnvironment)
        q1 = q1.options(contains_eager('personality_stage.personality.host_environment'))

        for cluster in q1.all():
            self.dict_of_impacted_envs.setdefault(
                cluster.personality_stage.personality.host_environment.name, []).append(cluster.status.name)

        q2 = session.query(Host)
        q2 = q2.filter(Host.services_used.contains(service_instance))
        q2 = q2.join(HostLifecycle)
        q2 = q2.options(contains_eager('status'))
        q2 = q2.join(PersonalityStage, Personality, HostEnvironment)
        q2 = q2.options(contains_eager('personality_stage.personality.host_environment'))

        for host in q2.all():
            self.dict_of_impacted_envs.setdefault(
                host.personality_stage.personality.host_environment.name, []).append(host.status.name)

    def validate_prod_feature(self, feature):
        session = object_session(feature)

        # validate that separately from command later
        q = session.query(Archetype)
        q = q.join(Archetype.features)
        q = q.filter_by(feature=feature)
        for dbarchetype in q:
            self.validate_prod_archetype(dbarchetype)

        q1 = session.query(Cluster)
        q1 = q1.join(ClusterLifecycle)
        q1 = q1.options(contains_eager('status'))
        q1 = q1.join(PersonalityStage)
        q1 = q1.join(PersonalityStage.features)
        q1 = q1.filter_by(feature=feature)
        q1 = q1.join(Personality, HostEnvironment)
        q1 = q1.options(contains_eager('personality_stage.personality.host_environment'))

        for cluster in q1.all():
            self.dict_of_impacted_envs.setdefault(
                cluster.personality_stage.personality.host_environment.name, []).append(cluster.status.name)

        q2 = session.query(Host)
        q2 = q2.join(PersonalityStage)
        q2 = q2.join(PersonalityStage.features)
        q2 = q2.filter_by(feature=feature)
        q2 = q2.join(Personality, HostEnvironment)
        q2 = q2.options(contains_eager('personality_stage.personality.host_environment'))

        for host in q2.all():
            self.dict_of_impacted_envs.setdefault(
                host.personality_stage.personality.host_environment.name, []).append(host.status.name)


ChangeManagement.handlers[Cluster] = ChangeManagement.validate_prod_cluster
ChangeManagement.handlers[ComputeCluster] = ChangeManagement.validate_prod_cluster
ChangeManagement.handlers[StorageCluster] = ChangeManagement.validate_prod_cluster
ChangeManagement.handlers[EsxCluster] = ChangeManagement.validate_prod_cluster
ChangeManagement.handlers[HostClusterMember] = ChangeManagement.validate_prod_cluster
ChangeManagement.handlers[MetaCluster] = ChangeManagement.validate_prod_cluster
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
ChangeManagement.handlers[Domain] = ChangeManagement.validate_default
