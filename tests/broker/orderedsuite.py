#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
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
"""
Module for testing the broker commands.

Ideally, real unit tests are self-contained.  In practice, for many of
these commands that would be painful.  The 'del' commands generally rely
on some 'add' commands having been run first.  The same holds for 'bind'
and 'unbind', 'map' and 'unmap', etc.
"""

from __future__ import absolute_import

import unittest
import os
from subprocess import Popen

from aquilon.config import Config

from .test_add_address import TestAddAddress
from .test_add_address_alias import TestAddAddressAlias
from .test_add_alias import TestAddAlias
from .test_add_allowed_personality import TestAddAllowedPersonality
from .test_add_application import TestAddApplication
from .test_add_aquilon_host import TestAddAquilonHost
from .test_add_archetype import TestAddArchetype
from .test_add_aurora_host import TestAddAuroraHost
from .test_add_auxiliary import TestAddAuxiliary
from .test_add_building import TestAddBuilding
from .test_add_building_preference import TestAddBuildingPreference
from .test_add_bunker import TestAddBunker
from .test_add_campus import TestAddCampus
from .test_add_chassis import TestAddChassis
from .test_add_city import TestAddCity
from .test_add_cluster import TestAddCluster
from .test_add_cluster_autostartlist import TestAddClusterAutoStartList
from .test_add_cluster_systemlist import TestAddClusterSystemList
from .test_add_console_server import TestAddConsoleServer
from .test_add_cpu import TestAddCpu
from .test_add_desk import TestAddDesk
from .test_add_disk import TestAddDisk
from .test_add_dns_domain import TestAddDnsDomain
from .test_add_dns_environment import TestAddDnsEnvironment
from .test_add_domain import TestAddDomain
from .test_add_dynamic_range import TestAddDynamicRange
from .test_add_entitlement import TestAddEntitlement
from .test_add_entitlement_type import TestAddEntitlementType
from .test_add_esx_cluster import TestAddESXCluster
from .test_add_feature import TestAddFeature
from .test_add_filesystem import TestAddFilesystem
from .test_add_host import TestAddHost
from .test_add_hostlink import TestAddHostlink
from .test_add_interface import TestAddInterface
from .test_add_interface_address import TestAddInterfaceAddress
from .test_add_intervention import TestAddIntervention
from .test_add_machine import TestAddMachine
from .test_add_manager import TestAddManager
from .test_add_metacluster import TestAddMetaCluster
from .test_add_model import TestAddModel
from .test_add_netdev import TestAddNetworkDevice
from .test_add_network import TestAddNetwork
from .test_add_network_compartment import TestAddNetworkCompartment
from .test_add_network_environment import TestAddNetworkEnvironment
from .test_add_ns_record import TestAddNSRecord
from .test_add_os import TestAddOS
from .test_add_parameter import TestAddParameter
from .test_add_parameter_definition import TestAddParameterDefinition
from .test_add_parameter_feature import TestAddParameterFeature
from .test_add_personality import TestAddPersonality
from .test_add_rack import TestAddRack
from .test_add_reboot_intervention import TestAddRebootIntervention
from .test_add_reboot_schedule import TestAddRebootSchedule
from .test_add_required_service import TestAddRequiredService
from .test_add_resourcegroup import TestAddResourceGroup
from .test_add_role import TestAddRole
from .test_add_room import TestAddRoom
from .test_add_router_address import TestAddRouterAddress
from .test_add_sandbox import TestAddSandbox
from .test_add_service import TestAddService
from .test_add_service_address import TestAddServiceAddress
from .test_add_service_address_sn_aliases import TestAddServiceAddressSNAliases
from .test_add_share import TestAddShare
from .test_add_shared_service_name import TestAddSharedServiceName
from .test_add_srv_record import TestAddSrvRecord
from .test_add_static_route import TestAddStaticRoute
from .test_add_user import TestAddUser
from .test_add_user_type import TestAddUserType
from .test_add_vendor import TestAddVendor
from .test_add_virtual_hardware import TestAddVirtualHardware
from .test_add_virtual_switch import TestAddVirtualSwitch
from .test_add_vlan import TestAddVlan
from .test_add_windows_host import TestAddWindowsHost
from .test_appliance import TestAppliance
from .test_audit import TestAudit
from .test_bind_client import TestBindClient
from .test_bind_cluster import TestBindCluster
from .test_bind_console_server import TestBindConsoleServer
from .test_bind_feature import TestBindFeature
from .test_bind_server import TestBindServer
from .test_build_clusters import TestBuildClusters
from .test_change_status import TestChangeStatus
from .test_change_status_cluster import TestChangeClusterStatus
from .test_client_bypass import TestClientBypass
from .test_client_failure import TestClientFailure
from .test_cluster import TestCluster
from .test_cm_logger import TestCMLogger
from .test_compile import TestCompile
from .test_consistency import TestConsistency
from .test_constraints_archetype import TestArchetypeConstraints
from .test_constraints_bind_client import TestBindClientConstraints
from .test_constraints_bind_server import TestBindServerConstraints
from .test_constraints_chooser import TestChooserConstraints
from .test_constraints_cluster import TestClusterConstraints
from .test_constraints_cluster_no_members import \
    TestClusterConstraintsNoMembers
from .test_constraints_cluster_no_vms import TestClusterConstraintsNoVMs
from .test_constraints_dns import TestDnsConstraints
from .test_constraints_domain import TestDomainConstraints
from .test_constraints_interface import TestInterfaceConstraints
from .test_constraints_location import TestLocationConstraints
from .test_constraints_machine import TestMachineConstraints
from .test_constraints_metacluster import TestMetaClusterConstraints
from .test_constraints_model import TestModelConstraints
from .test_constraints_netdev import TestNetworkDeviceConstraints
from .test_constraints_network import TestNetworkConstraints
from .test_constraints_parameter import TestParameterConstraints
from .test_constraints_personality import TestPersonalityConstraints
from .test_constraints_service import TestServiceConstraints
from .test_constraints_umask import TestUmaskConstraints
from .test_constraints_vendor import TestVendorConstraints
from .test_continent import TestContinent
from .test_copy_personality import TestCopyPersonality
from .test_country import TestCountry
from .test_del_10gig_hardware import TestDel10GigHardware
from .test_del_address import TestDelAddress
from .test_del_address_alias import TestDelAddressAlias
from .test_del_alias import TestDelAlias
from .test_del_allowed_personality import TestDelAllowedPersonality
from .test_del_application import TestDelApplication
from .test_del_archetype import TestDelArchetype
from .test_del_auxiliary import TestDelAuxiliary
from .test_del_building import TestDelBuilding
from .test_del_building_preference import TestDelBuildingPreference
from .test_del_bunker import TestDelBunker
from .test_del_campus import TestDelCampus
from .test_del_chassis import TestDelChassis
from .test_del_city import TestDelCity
from .test_del_cluster import TestDelCluster
from .test_del_cluster_autostartlist import TestDelClusterAutoStartList
from .test_del_cluster_systemlist import TestDelClusterSystemList
from .test_del_console_server import TestDelConsoleServer
from .test_del_desk import TestDelDesk
from .test_del_disk import TestDelDisk
from .test_del_dns_domain import TestDelDnsDomain
from .test_del_dns_environment import TestDelDnsEnvironment
from .test_del_domain import TestDelDomain
from .test_del_dynamic_range import TestDelDynamicRange
from .test_del_entitlement import TestDelEntitlement
from .test_del_entitlement_type import TestDelEntitlementType
from .test_del_esx_cluster import TestDelESXCluster
from .test_del_feature import TestDelFeature
from .test_del_filesystem import TestDelFilesystem
from .test_del_host import TestDelHost
from .test_del_hostlink import TestDelHostlink
from .test_del_interface import TestDelInterface
from .test_del_interface_address import TestDelInterfaceAddress
from .test_del_intervention import TestDelIntervention
from .test_del_machine import TestDelMachine
from .test_del_manager import TestDelManager
from .test_del_metacluster import TestDelMetaCluster
from .test_del_model import TestDelModel
from .test_del_netdev import TestDelNetworkDevice
from .test_del_network import TestDelNetwork
from .test_del_network_compartment import TestDelNetworkCompartment
from .test_del_network_environment import TestDelNetworkEnvironment
from .test_del_ns_record import TestDelNSRecord
from .test_del_os import TestDelOS
from .test_del_parameter import TestDelParameter
from .test_del_parameter_definition import TestDelParameterDefinition
from .test_del_parameter_feature import TestDelParameterFeature
from .test_del_personality import TestDelPersonality
from .test_del_rack import TestDelRack
from .test_del_reboot_intervention import TestDelRebootIntervention
from .test_del_reboot_schedule import TestDelRebootSchedule
from .test_del_required_service import TestDelRequiredService
from .test_del_resourcegroup import TestDelResourceGroup
from .test_del_role import TestDelRole
from .test_del_room import TestDelRoom
from .test_del_router_address import TestDelRouterAddress
from .test_del_sandbox import TestDelSandbox
from .test_del_service import TestDelService
from .test_del_service_address import TestDelServiceAddress
from .test_del_service_address_sn_aliases import TestDelServiceAddressSNAliases
from .test_del_share import TestDelShare
from .test_del_shared_service_name import TestDelSharedServiceName
from .test_del_srv_record import TestDelSrvRecord
from .test_del_static_route import TestDelStaticRoute
from .test_del_user import TestDelUser
from .test_del_user_type import TestDelUserType
from .test_del_vendor import TestDelVendor
from .test_del_virtual_hardware import TestDelVirtualHardware
from .test_del_virtual_switch import TestDelVirtualSwitch
from .test_del_vlan import TestDelVlan
from .test_del_windows_host import TestDelWindowsHost
from .test_demolish_clusters import TestDemolishClusters
from .test_deploy_domain import TestDeployDomain
from .test_deprecated_switch import TestDeprecatedSwitch
from .test_discover_netdev import TestDiscoverNetworkDevice
from .test_documentation import TestDocumentation
from .test_dump_dns import TestDumpDns
from .test_flush import TestFlush
from .test_get import TestGet
from .test_grns import TestGrns
from .test_hub import TestHub
from .test_justification import TestJustification
from .test_make import TestMake
from .test_make_aquilon import TestMakeAquilon
from .test_make_cluster import TestMakeCluster
from .test_manage import TestManage
from .test_manage_list import TestManageList
from .test_manage_validate_branch import TestManageValidateBranch
from .test_map_grn import TestMapGrn
from .test_map_service import TestMapService
from .test_merge_conflicts import TestMergeConflicts
from .test_organization import TestOrganization
from .test_permission import TestPermission
from .test_ping import TestPing
from .test_poll_netdev import TestPollNetworkDevice
from .test_prebind_server import TestPrebindServer
from .test_profile import TestProfile
from .test_publish_sandbox import TestPublishSandbox
from .test_pxeswitch import TestPxeswitch
from .test_rebind_client import TestRebindClient
from .test_rebind_cluster import TestRebindCluster
from .test_rebind_metacluster import TestRebindMetaCluster
from .test_reconfigure import TestReconfigure
from .test_refresh_network import TestRefreshNetwork
from .test_refresh_user import TestRefreshUser
from .test_rename_netdev import TestRenameNetworkDevice
from .test_reset_advertised_status import TestResetAdvertisedStatus
from .test_restart import TestBrokerReStart
from .test_root_access import TestRootAccess
from .test_search_building import TestSearchBuilding
from .test_search_cluster import TestSearchCluster
from .test_search_cluster_esx import TestSearchClusterESX
from .test_search_dns import TestSearchDns
from .test_search_esx_cluster import TestSearchESXCluster
from .test_search_hardware import TestSearchHardware
from .test_search_host import TestSearchHost
from .test_search_machine import TestSearchMachine
from .test_search_metacluster import TestSearchMetaCluster
from .test_search_model import TestSearchModel
from .test_search_netdev import TestSearchNetworkDevice
from .test_search_network import TestSearchNetwork
from .test_search_next import TestSearchNext
from .test_search_observed_mac import TestSearchObservedMac
from .test_search_personality import TestSearchPersonality
from .test_search_rack import TestSearchRack
from .test_search_resource import TestSearchResource
from .test_search_service import TestSearchService
from .test_search_system import TestSearchSystem
from .test_setup_params import TestSetupParams
from .test_show_active_commands import TestShowActiveCommands
from .test_show_campus import TestShowCampus
from .test_show_fqdn import TestShowFqdn
from .test_show_machine import TestShowMachine
from .test_show_netdev import TestShowNetworkDevice
from .test_show_network import TestShowNetwork
from .test_show_permission import TestShowPermission
from .test_show_review import TestShowReview
from .test_show_service_all import TestShowServiceAll
from .test_split_merge_network import TestSplitMergeNetwork
from .test_start import TestBrokerStart
from .test_status import TestStatus
from .test_stop import TestBrokerStop
from .test_sync_domain import TestSyncDomain
from .test_unbind_client import TestUnbindClient
from .test_unbind_cluster import TestUnbindCluster
from .test_unbind_feature import TestUnbindFeature
from .test_unbind_server import TestUnbindServer
from .test_uncluster import TestUncluster
from .test_unmap_service import TestUnmapService
from .test_update_address import TestUpdateAddress
from .test_update_address_alias import TestUpdateAddressAlias
from .test_update_alias import TestUpdateAlias
from .test_update_archetype import TestUpdateArchetype
from .test_update_branch import TestUpdateBranch
from .test_update_building import TestUpdateBuilding
from .test_update_building_preference import TestUpdateBuildingPreference
from .test_update_campus import TestUpdateCampus
from .test_update_chassis import TestUpdateChassis
from .test_update_cluster import TestUpdateCluster
from .test_update_cluster_autostartlist import TestUpdateClusterAutoStartList
from .test_update_cluster_systemlist import TestUpdateClusterSystemList
from .test_update_console_server import TestUpdateConsoleServer
from .test_update_disk import TestUpdateDisk
from .test_update_dns_environment import TestUpdateDnsEnvironment
from .test_update_entitlement_type import TestUpdateEntitlementType
from .test_update_esx_cluster import TestUpdateESXCluster
from .test_update_feature import TestUpdateFeature
from .test_update_filesystem import TestUpdateFilesystem
from .test_update_interface import TestUpdateInterface
from .test_update_machine import TestUpdateMachine
from .test_update_metacluster import TestUpdateMetaCluster
from .test_update_model import TestUpdateModel
from .test_update_netdev import TestUpdateNetworkDevice
from .test_update_netdev_mac import TestUpdateNetworkDeviceMac
from .test_update_network import TestUpdateNetwork
from .test_update_network_compartment import TestUpdateNetworkCompartment
from .test_update_network_environment import TestUpdateNetworkEnvironment
from .test_update_os import TestUpdateOS
from .test_update_parameter import TestUpdateParameter
from .test_update_parameter_definition import TestUpdateParameterDefinition
from .test_update_parameter_feature import TestUpdateParameterFeature
from .test_update_personality import TestUpdatePersonality
from .test_update_rack import TestUpdateRack
from .test_update_router_address import TestUpdateRouterAddress
from .test_update_service import TestUpdateService
from .test_update_service_address import TestUpdateServiceAddress
from .test_update_srv_record import TestUpdateSrvRecord
from .test_usecase_anycast import TestUsecaseAnycast
from .test_usecase_database import TestUsecaseDatabase
from .test_usecase_hacluster import TestUsecaseHACluster
from .test_usecase_networks import TestUsecaseNetworks
from .test_vm_migration import TestVMMigration
from .test_vulcan2 import TestVulcan20
from .test_vulcan_localdisk import TestVulcanLocalDisk


class BrokerTestSuite(unittest.TestSuite):
    """Set up the broker's unit tests in an order that allows full coverage.

    The general strategy is to start the broker, test adding things,
    test deleting things, and then shut down the broker.  Most of the show
    commands are tested as verification tests in add/del tests.  Those that
    are not have explicit tests between add and delete.

    """
    test_start = [TestBrokerStart,
                  TestPing, TestStatus]
    test_restart = [TestBrokerReStart,
                    TestPing, TestStatus]
    test_stop = [TestBrokerStop]
    test_list = [TestAddRole, TestPermission,
                 TestAddDnsDomain, TestAddDnsEnvironment,
                 TestAddUserType, TestAddUser, TestShowPermission,
                 TestAddEntitlementType,
                 TestUpdateEntitlementType,
                 TestAddSandbox, TestAddDomain, TestUpdateBranch,
                 TestCMLogger,
                 TestGet, TestPublishSandbox, TestDeployDomain,
                 TestSyncDomain,
                 TestMergeConflicts,
                 TestGrns,
                 TestAddArchetype, TestAddOS,
                 TestAddFeature,
                 TestAddParameterDefinition, TestSetupParams,
                 TestAddService, TestAddPersonality, TestAddRequiredService,
                 TestAddParameter,
                 TestOrganization, TestHub, TestContinent, TestCountry,
                 TestAddCampus, TestAddCity,
                 TestAddBuilding, TestAddRoom, TestAddBunker,
                 TestAddRack, TestAddDesk,
                 TestAddVendor, TestAddCpu, TestAddModel,
                 TestAddNetworkCompartment,
                 TestAddNetworkEnvironment, TestAddNetwork,
                 TestAddNSRecord,
                 TestAddVlan,
                 TestAddVirtualSwitch,
                 TestAddMetaCluster, TestAddESXCluster,
                 TestAddCluster,
                 TestClusterConstraintsNoMembers,
                 TestDeprecatedSwitch,
                 TestAddChassis,
                 TestAddConsoleServer,
                 TestAddNetworkDevice, TestUpdateNetworkDevice,
                 TestUpdateChassis,
                 TestUpdateConsoleServer,
                 TestAddMachine, TestAddDisk, TestAddInterface,
                 TestAddAddress,
                 TestAddRouterAddress, TestAddDynamicRange,
                 TestAddAquilonHost, TestAddWindowsHost, TestAddAuroraHost,
                 TestPollNetworkDevice,
                 TestUpdateNetworkDeviceMac,
                 TestAddHost,
                 TestAddAuxiliary, TestAddManager, TestAddInterfaceAddress,
                 TestAddServiceAddress,
                 TestRenameNetworkDevice, TestDiscoverNetworkDevice,
                 TestAddAlias,
                 TestAddAddressAlias,
                 TestAddSrvRecord,
                 TestMapService, TestBindClient, TestPrebindServer,
                 TestAddResourceGroup, TestAddShare, TestAddFilesystem,
                 TestAddApplication, TestAddIntervention,
                 TestAddHostlink, TestAddRebootSchedule, TestAddRebootIntervention,
                 TestAddSharedServiceName, TestAddServiceAddressSNAliases,
                 TestFlush,
                 TestMakeAquilon, TestMakeCluster, TestCluster,
                 TestAddAllowedPersonality,
                 TestDelAllowedPersonality,
                 TestBindCluster, TestChangeClusterStatus, TestRebindCluster,
                 TestMake,
                 TestAddStaticRoute,
                 TestMapGrn,
                 TestRebindMetaCluster,
                 TestUpdateCampus, TestUpdateBuilding,
                 TestUpdateOS,
                 TestBuildClusters, TestAddBuildingPreference,
                 TestAddClusterAutoStartList, TestAddClusterSystemList,
                 TestClusterConstraintsNoVMs,
                 TestAddVirtualHardware,
                 TestVulcanLocalDisk,
                 TestVulcan20,
                 TestAppliance,
                 TestUnbindClient, TestRebindClient, TestReconfigure,
                 TestChangeStatus, TestResetAdvertisedStatus,
                 TestBindFeature,
                 TestAddParameterFeature,
                 TestJustification,
                 TestChooserConstraints,
                 TestCompile,
                 TestProfile,
                 TestBindServer,
                 TestServiceConstraints,
                 TestBindClientConstraints, TestBindServerConstraints,
                 TestArchetypeConstraints, TestPersonalityConstraints,
                 TestParameterConstraints,
                 TestDomainConstraints,
                 TestVendorConstraints, TestModelConstraints,
                 TestMachineConstraints, TestNetworkDeviceConstraints,
                 TestInterfaceConstraints,
                 TestUpdatePersonality, TestCopyPersonality,
                 TestClusterConstraints, TestMetaClusterConstraints,
                 TestLocationConstraints,
                 TestDnsConstraints,
                 TestShowServiceAll, TestShowCampus, TestShowFqdn,
                 TestSearchBuilding,
                 TestSearchRack,
                 TestShowNetwork,
                 TestShowNetworkDevice, TestSearchNetworkDevice,
                 TestSearchHardware, TestSearchMachine, TestShowMachine,
                 TestShowReview,
                 TestSearchDns, TestDumpDns,
                 TestSearchPersonality,
                 TestSearchSystem, TestSearchHost, TestSearchESXCluster,
                 TestSearchClusterESX, TestSearchCluster,
                 TestSearchMetaCluster,
                 TestSearchObservedMac, TestSearchNext, TestSearchNetwork,
                 TestSearchModel,
                 TestSearchService,
                 TestSearchResource,
                 TestUpdateInterface, TestUpdateMachine, TestVMMigration,
                 TestUpdateModel,
                 TestUpdateDisk,
                 TestUpdateRack,
                 TestBindConsoleServer,
                 TestUpdateAlias, TestUpdateSrvRecord, TestUpdateAddress,
                 TestUpdateAddressAlias,
                 TestUpdateServiceAddress,
                 TestUpdateFilesystem,
                 TestUpdateClusterAutoStartList,
                 TestUpdateClusterSystemList,
                 TestUpdateNetworkCompartment,
                 TestRefreshNetwork, TestUpdateNetwork, TestSplitMergeNetwork,
                 TestNetworkConstraints,
                 TestUpdateService,
                 TestUpdateNetworkEnvironment, TestUpdateDnsEnvironment,
                 TestUpdateRouterAddress,
                 TestUpdateArchetype,
                 TestUpdateFeature,
                 TestUpdateParameterDefinition, TestUpdateParameter,
                 TestUpdateParameterFeature,
                 TestUpdateMetaCluster, TestUpdateESXCluster,
                 TestUpdateCluster, TestUpdateBuildingPreference,
                 TestPxeswitch, TestManage, TestManageValidateBranch,
                 TestManageList,
                 TestRefreshUser, TestRootAccess,
                 TestAddEntitlement,
                 TestDelEntitlement,
                 TestDelEntitlementType,
                 TestUsecaseDatabase, TestUsecaseHACluster,
                 TestUsecaseAnycast,
                 TestUsecaseNetworks,
                 TestClientBypass,
                 TestConsistency,
                 TestUmaskConstraints,
                 TestDelClusterAutoStartList, TestDelClusterSystemList,
                 TestDelBuildingPreference, TestDemolishClusters,
                 TestUnbindServer, TestUnmapService,
                 TestDelParameterFeature,
                 TestUnbindFeature,
                 TestDel10GigHardware, TestDelVirtualHardware,
                 TestUnbindCluster, TestUncluster,
                 TestDelServiceAddressSNAliases, TestDelSharedServiceName,
                 TestDelShare, TestDelFilesystem,
                 TestDelHostlink, TestDelRebootIntervention, TestDelRebootSchedule,
                 TestDelIntervention, TestDelApplication,
                 TestDelResourceGroup,
                 TestDelStaticRoute,
                 TestDelServiceAddress, TestDelInterfaceAddress,
                 TestDelDynamicRange, TestDelSrvRecord, TestDelAlias,
                 TestDelAddressAlias,
                 TestDelAddress, TestDelNSRecord,
                 TestDelManager, TestDelAuxiliary, TestDelWindowsHost, TestDelHost,
                 TestDelInterface, TestDelDisk, TestDelMachine, TestDelChassis,
                 TestDelConsoleServer,
                 TestDelNetworkDevice,
                 TestDelCluster,
                 TestDelESXCluster, TestDelMetaCluster,
                 TestDelVirtualSwitch,
                 TestDelRouterAddress, TestDelNetwork, TestDelNetworkEnvironment,
                 TestDelNetworkCompartment,
                 TestDelVlan,
                 TestDelModel, TestDelVendor,
                 TestDelParameter, TestDelParameterDefinition,
                 TestDelFeature,
                 TestDelDesk, TestDelRack, TestDelBunker, TestDelRoom,
                 TestDelBuilding, TestDelRequiredService,
                 TestDelCity, TestDelCampus,
                 TestDelPersonality, TestDelOS, TestDelArchetype,
                 TestDelService,
                 TestDelDomain, TestDelSandbox,
                 TestDelUser, TestDelUserType,
                 TestDelDnsEnvironment, TestDelDnsDomain, TestDelRole,
                 TestClientFailure, TestAudit, TestShowActiveCommands,
                 TestDocumentation]

    def __init__(self, start=None, resume=False, single=False,
                 *args, **kwargs):
        if resume and not start:
            raise ValueError('Cannot resume without a start test given.')
        # Initialise.
        unittest.TestSuite.__init__(self, *args, **kwargs)

        # Add the required set of non-optional, initialising tests depending on
        # whether the testing is to be resumed after a prior failed test run or
        # not.  NB: this set of tests precedes the test given with 'start' (or
        # test 0 if 'start' not given).
        for case in (self.test_start, self.test_restart)[resume]:
            self.addTest(unittest.TestLoader().loadTestsFromTestCase(case))
        # Load the first (after the required start/restart set) test (and the
        # remaining tests in case of single not true.  This is either test 0 or
        # the test given with 'start'.
        if start:
            # Find indices for the given (in the 'TestCase.test_method format')
            # start method.  The first index we need points to the given test
            # case (stored in self.test_list).  The second one is the index of
            # the given test method (on a sorted list of all test methods
            # defined in the test case class).
            start_indices = self._get_case_and_method_indices(start)
        else:
            start_indices = 0, 0
        # Load the given start, or the test with index 0, 0.
        method_list = list(
            unittest.TestLoader().loadTestsFromTestCase(
                self.test_list[start_indices[0]])
        )
        # We want all the subsequent methods from the selected test
        # case unless single is True, in which case we do not want to load any
        # more methods.
        last_method_index = start_indices[1] + 1 if single else None
        self.addTests(
            list(method_list)[start_indices[1]:last_method_index]
        )

        # When appropriate, load tests from all the remaining (sans stop) test
        # cases.
        # We do not want to load any other (than the stop) tests in case of
        # single.
        if single:
            end_case_index = start_indices[0]
        else:
            end_case_index = len(self.test_list)
        for i in range(start_indices[0] + 1, end_case_index):
            self.addTest(unittest.TestLoader().loadTestsFromTestCase(
                self.test_list[i]))

        # Add the required end test(s).
        for case in self.test_stop:
            self.addTest(unittest.TestLoader().loadTestsFromTestCase(case))

    def _get_case_and_method_indices(self, case_and_method):
        try:
            case_name, method_name = case_and_method.split('.')
            case_index = [test.__name__ for test in self.test_list
                          ].index(case_name)
            method_list = list(
                unittest.TestLoader().loadTestsFromTestCase(
                    self.test_list[case_index])
            )
            # noinspection PyProtectedMember
            method_index = [method._testMethodName for method in method_list
                            ].index(method_name)
        except ValueError:
            raise ValueError(
                'Invalid value of the "start" parameter. Please pass --start '
                'YourSelectedTestCase.your_selected_test_method, to [re]start '
                'testing from the specified test.')
        return case_index, method_index
