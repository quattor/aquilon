#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""
Module for testing the broker commands.

Ideally, real unit tests are self-contained.  In practice, for many of
these commands that would be painful.  The 'del' commands generally rely
on some 'add' commands having been run first.  The same holds for 'bind'
and 'unbind', 'map' and 'unmap', etc.
"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(__file__))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))
    sys.path.append(os.path.join(SRCDIR, "tests"))
    import depends

from test_start import TestBrokerStart
from test_ping import TestPing
from test_status import TestStatus
from test_show_active_commands import TestShowActiveCommands
from test_permission import TestPermission
from test_add_dns_domain import TestAddDnsDomain
from test_add_dns_environment import TestAddDnsEnvironment
from test_add_sandbox import TestAddSandbox
from test_add_domain import TestAddDomain
from test_update_branch import TestUpdateBranch
from test_get import TestGet
from test_publish_sandbox import TestPublishSandbox
from test_deploy_domain import TestDeployDomain
from test_sync_domain import TestSyncDomain
from test_merge_conflicts import TestMergeConflicts
from test_add_archetype import TestAddArchetype
from test_add_os import TestAddOS
from test_add_personality import TestAddPersonality
from test_add_service import TestAddService
from test_update_service import TestUpdateService
from test_add_required_service import TestAddRequiredService
from test_organization import TestOrganization
from test_add_building import TestAddBuilding
from test_add_city import TestAddCity
from test_add_room import TestAddRoom
from test_add_location import TestAddLocation
from test_add_rack import TestAddRack
from test_add_vendor import TestAddVendor
from test_add_cpu import TestAddCpu
from test_add_model import TestAddModel
from test_add_network import TestAddNetwork
from test_add_ns_record import TestAddNSRecord
from test_add_router import TestAddRouter
from test_add_metacluster import TestAddMetaCluster
from test_add_esx_cluster import TestAddESXCluster
from test_add_esx_cluster_aligned_service import (
    TestAddESXClusterAlignedService)
from test_early_constraints_cluster import TestClusterEarlyConstraints
from test_add_tor_switch import TestAddTorSwitch
from test_add_switch import TestAddSwitch
from test_update_switch import TestUpdateSwitch
from test_poll_switch import TestPollSwitch
from test_add_chassis import TestAddChassis
from test_add_machine import TestAddMachine
from test_add_disk import TestAddDisk
from test_add_interface import TestAddInterface
from test_add_address import TestAddAddress
from test_add_dynamic_range import TestAddDynamicRange
from test_add_host import TestAddHost
from test_add_aquilon_host import TestAddAquilonHost
from test_add_windows_host import TestAddWindowsHost
from test_add_aurora_host import TestAddAuroraHost
from test_add_auxiliary import TestAddAuxiliary
from test_add_interface_address import TestAddInterfaceAddress
from test_add_manager import TestAddManager
from test_map_service import TestMapService
from test_bind_client import TestBindClient
from test_prebind_server import TestPrebindServer
from test_make_aquilon import TestMakeAquilon
from test_make import TestMake
from test_make_cluster import TestMakeCluster
from test_cluster import TestCluster
from test_bind_esx_cluster import TestBindESXCluster
from test_change_status_cluster import TestChangeClusterStatus
from test_rebind_esx_cluster import TestRebindESXCluster
from test_rebind_metacluster import TestRebindMetaCluster
from test_add_virtual_hardware import TestAddVirtualHardware
from test_add_10gig_hardware import TestAdd10GigHardware
from test_unbind_client import TestUnbindClient
from test_rebind_client import TestRebindClient
from test_reconfigure import TestReconfigure
from test_change_status import TestChangeStatus
from test_refresh_windows_hosts import TestRefreshWindowsHosts
from test_constraints_chooser import TestChooserConstraints
from test_flush import TestFlush
from test_compile import TestCompile
from test_profile import TestProfile
from test_bind_server import TestBindServer
from test_constraints_bind_client import TestBindClientConstraints
from test_constraints_bind_server import TestBindServerConstraints
from test_constraints_archetype import TestArchetypeConstraints
from test_constraints_personality import TestPersonalityConstraints
from test_constraints_service import TestServiceConstraints
from test_constraints_domain import TestDomainConstraints
from test_constraints_vendor import TestVendorConstraints
from test_constraints_machine import TestMachineConstraints
from test_constraints_interface import TestInterfaceConstraints
from test_constraints_switch import TestSwitchConstraints
from test_constraints_make import TestMakeConstraints
from test_constraints_cluster import TestClusterConstraints
from test_constraints_metacluster import TestMetaClusterConstraints
from test_constraints_location import TestLocationConstraints
from test_constraints_dns import TestDnsConstraints
from test_show_hostiplist import TestShowHostIPList
from test_show_hostmachinelist import TestShowHostMachineList
from test_show_machinemaclist import TestShowMachineMacList
from test_show_service_all import TestShowServiceAll
from test_show_campus import TestShowCampus
from test_show_fqdn import TestShowFqdn
from test_show_switch import TestShowSwitch
from test_show_machine import TestShowMachine
from test_search_switch import TestSearchSwitch
from test_search_hardware import TestSearchHardware
from test_search_machine import TestSearchMachine
from test_search_system import TestSearchSystem
from test_search_host import TestSearchHost
from test_search_esx_cluster import TestSearchESXCluster
from test_search_observed_mac import TestSearchObservedMac
from test_search_next import TestSearchNext
from test_search_network import TestSearchNetwork
from test_refresh_network import TestRefreshNetwork
from test_update_interface import TestUpdateInterface
from test_update_machine import TestUpdateMachine
from test_update_model import TestUpdateModel
from test_update_rack import TestUpdateRack
from test_update_network import TestUpdateNetwork
from test_update_archetype import TestUpdateArchetype
from test_update_personality import TestUpdatePersonality
from test_update_metacluster import TestUpdateMetaCluster
from test_update_esx_cluster import TestUpdateESXCluster
from test_pxeswitch import TestPxeswitch
from test_manage import TestManage
from test_constraints_umask import TestUmaskConstraints
from test_unbind_server import TestUnbindServer
from test_unmap_service import TestUnmapService
from test_del_10gig_hardware import TestDel10GigHardware
from test_del_virtual_hardware import TestDelVirtualHardware
from test_unbind_esx_cluster import TestUnbindESXCluster
from test_uncluster import TestUncluster
from test_del_dynamic_range import TestDelDynamicRange
from test_del_address import TestDelAddress
from test_del_city import TestDelCity
from test_del_manager import TestDelManager
from test_del_auxiliary import TestDelAuxiliary
from test_del_host import TestDelHost
from test_del_interface import TestDelInterface
from test_del_interface_address import TestDelInterfaceAddress
from test_del_disk import TestDelDisk
from test_del_machine import TestDelMachine
from test_del_chassis import TestDelChassis
from test_del_switch import TestDelSwitch
from test_del_esx_cluster_aligned_service import (
    TestDelESXClusterAlignedService)
from test_del_esx_cluster import TestDelESXCluster
from test_del_metacluster import TestDelMetaCluster
from test_del_router import TestDelRouter
from test_del_network import TestDelNetwork
from test_del_model import TestDelModel
from test_del_cpu import TestDelCpu
from test_del_vendor import TestDelVendor
from test_del_rack import TestDelRack
from test_del_room import TestDelRoom
from test_del_building import TestDelBuilding
from test_del_required_service import TestDelRequiredService
from test_del_service import TestDelService
from test_del_personality import TestDelPersonality
from test_del_os import TestDelOS
from test_del_archetype import TestDelArchetype
from test_del_domain import TestDelDomain
from test_del_sandbox import TestDelSandbox
from test_del_ns_record import TestDelNSRecord
from test_del_dns_domain import TestDelDnsDomain
from test_del_dns_environment import TestDelDnsEnvironment
from test_client_failure import TestClientFailure
from test_client_bypass import TestClientBypass
from test_stop import TestBrokerStop


class BrokerTestSuite(unittest.TestSuite):
    """Set up the broker's unit tests in an order that allows full coverage.

    The general strategy is to start the broker, test adding things,
    test deleting things, and then shut down the broker.  Most of the show
    commands are tested as verification tests in add/del tests.  Those that
    are not have explicit tests between add and delete.

    """

    def __init__(self, *args, **kwargs):
        unittest.TestSuite.__init__(self, *args, **kwargs)
        for test in [TestBrokerStart,
                TestPing, TestStatus, TestShowActiveCommands,
                TestPermission,
                TestAddDnsDomain, TestAddDnsEnvironment,
                TestAddSandbox, TestAddDomain, TestUpdateBranch,
                TestGet, TestPublishSandbox, TestDeployDomain,
                TestSyncDomain,
                TestMergeConflicts,
                TestAddArchetype, TestAddOS, TestAddPersonality,
                TestAddService, TestUpdateService, TestAddRequiredService,
                TestAddCity,
                TestAddBuilding, TestAddRoom, TestAddLocation,
                TestAddRack, TestAddVendor, TestAddCpu, TestAddModel,
                TestAddNetwork, TestAddNSRecord,
                TestAddMetaCluster, TestAddESXCluster,
                TestAddESXClusterAlignedService,
                TestClusterEarlyConstraints,
                TestAddTorSwitch, TestAddSwitch, TestUpdateSwitch,
                TestPollSwitch,
                TestAddChassis, TestAddMachine, TestAddDisk, TestAddInterface,
                TestAddAddress, TestAddRouter, TestAddDynamicRange, TestAddHost,
                TestAddAquilonHost, TestAddWindowsHost, TestAddAuroraHost,
                TestAddAuxiliary, TestAddManager, TestAddInterfaceAddress,
                TestMapService, TestBindClient, TestPrebindServer,
                TestServiceConstraints,
                TestFlush,
                TestMakeAquilon, TestMakeCluster, TestCluster,
                TestBindESXCluster, TestChangeClusterStatus, TestRebindESXCluster,
                TestMake,
                TestRebindMetaCluster,
                TestAddVirtualHardware, TestAdd10GigHardware,
                TestUnbindClient, TestRebindClient, TestReconfigure,
                TestChangeStatus,
                TestRefreshWindowsHosts,
                TestChooserConstraints,
                TestCompile,
                TestProfile,
                TestBindServer,
                TestBindClientConstraints, TestBindServerConstraints,
                TestArchetypeConstraints, TestPersonalityConstraints,
                TestDomainConstraints, TestVendorConstraints,
                TestMachineConstraints, TestSwitchConstraints,
                TestInterfaceConstraints,
                TestMakeConstraints,
                TestUpdatePersonality,
                TestClusterConstraints, TestMetaClusterConstraints,
                TestLocationConstraints,
                TestDnsConstraints,
                TestShowHostIPList, TestShowHostMachineList, TestShowMachineMacList,
                TestShowServiceAll, TestShowCampus, TestShowFqdn,
                TestShowSwitch, TestSearchSwitch,
                TestSearchHardware, TestSearchMachine, TestShowMachine,
                TestSearchSystem, TestSearchHost, TestSearchESXCluster,
                TestSearchObservedMac, TestSearchNext, TestSearchNetwork,
                TestUpdateInterface, TestUpdateMachine, TestUpdateModel,
                TestUpdateRack,
                TestRefreshNetwork, TestUpdateNetwork,
                TestUpdateArchetype,
                TestUpdateMetaCluster, TestUpdateESXCluster,
                TestPxeswitch, TestManage,
                TestClientBypass,
                TestUmaskConstraints,
                TestUnbindServer, TestUnmapService,
                TestDel10GigHardware, TestDelVirtualHardware,
                TestUnbindESXCluster, TestUncluster,
                TestDelInterfaceAddress,
                TestDelDynamicRange, TestDelAddress,
                TestDelManager, TestDelAuxiliary, TestDelHost,
                TestDelInterface, TestDelDisk, TestDelMachine, TestDelChassis,
                TestDelSwitch,
                TestDelESXClusterAlignedService,
                TestDelESXCluster, TestDelMetaCluster,
                TestDelRouter, TestDelNetwork,
                TestDelModel, TestDelCpu, TestDelVendor,
                TestDelRack, TestDelRoom,
                TestDelBuilding, TestDelRequiredService, TestDelService,
                TestDelCity,
                TestDelPersonality, TestDelOS, TestDelArchetype,
                TestDelDomain, TestDelSandbox,
                TestDelNSRecord, TestDelDnsEnvironment, TestDelDnsDomain,
                TestClientFailure,
                TestBrokerStop]:
            self.addTest(unittest.TestLoader().loadTestsFromTestCase(test))


if __name__=='__main__':
    suite = BrokerTestSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
