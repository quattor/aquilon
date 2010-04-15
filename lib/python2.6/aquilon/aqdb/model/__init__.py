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
from aquilon.aqdb.model.base import Base
from aquilon.aqdb.model.stateengine import StateEngine

#AUTHORIZATION
from aquilon.aqdb.model.role import Role
from aquilon.aqdb.model.realm import Realm
from aquilon.aqdb.model.user_principal import UserPrincipal

#LOCATION
from aquilon.aqdb.model.location import Location
from aquilon.aqdb.model.company import Company
from aquilon.aqdb.model.hub import Hub
from aquilon.aqdb.model.continent import Continent
from aquilon.aqdb.model.country import Country
from aquilon.aqdb.model.city import City
from aquilon.aqdb.model.building import Building
from aquilon.aqdb.model.room import Room
from aquilon.aqdb.model.campus import Campus
from aquilon.aqdb.model.rack import Rack
from aquilon.aqdb.model.desk import Desk

#NETWORK
from aquilon.aqdb.model.network import Network
from aquilon.aqdb.model.dns_domain import DnsDomain

#CONFIG
from aquilon.aqdb.model.archetype import Archetype
from aquilon.aqdb.model.personality import Personality
from aquilon.aqdb.model.operating_system import OperatingSystem

#SYSTEM
from aquilon.aqdb.model.system import (System, DynamicStub, FutureARecord,
                                       ReservedName)

#HARDWARE
from aquilon.aqdb.model.vendor import Vendor
from aquilon.aqdb.model.model import Model
from aquilon.aqdb.model.hardware_entity import HardwareEntity
from aquilon.aqdb.model.cpu import Cpu
from aquilon.aqdb.model.machine import Machine
from aquilon.aqdb.model.hostlifecycle import HostLifecycle
from aquilon.aqdb.model.switch_hw import SwitchHw
from aquilon.aqdb.model.chassis_hw import ChassisHw

#SYSTEM
from aquilon.aqdb.model.chassis import Chassis
from aquilon.aqdb.model.manager import Manager
from aquilon.aqdb.model.branch import Branch, Domain, Sandbox
from aquilon.aqdb.model.host import Host
from aquilon.aqdb.model.switch import Switch

from aquilon.aqdb.model.primary_name_association import PrimaryNameAssociation

#HARDWARE/SYSTEM LINKAGES
from aquilon.aqdb.model.observed_mac import ObservedMac
from aquilon.aqdb.model.vlan import ObservedVlan, VlanInfo
from aquilon.aqdb.model.chassis_slot import ChassisSlot
from aquilon.aqdb.model.interface import Interface
from aquilon.aqdb.model.auxiliary import Auxiliary

#SERVICE
from aquilon.aqdb.model.service import (Service, ServiceListItem,
                                        PersonalityServiceListItem)
from aquilon.aqdb.model.service_instance import ServiceInstance, BuildItem
from aquilon.aqdb.model.service_instance_server import ServiceInstanceServer
from aquilon.aqdb.model.service_map import ServiceMap
from aquilon.aqdb.model.personality_service_map import PersonalityServiceMap

#NasDisk depends on ServiceInstance
from aquilon.aqdb.model.disk import Disk, LocalDisk, NasDisk

#CLUSTER
from aquilon.aqdb.model.clusterlifecycle import ClusterLifecycle
from aquilon.aqdb.model.cluster import (Cluster, EsxCluster,
                                        HostClusterMember,
                                        MachineClusterMember,
                                        ClusterAlignedService,
                                        ClusterServiceBinding)
from aquilon.aqdb.model.personality_cluster_info import (PersonalityClusterInfo,
                                                         PersonalityESXClusterInfo)

from aquilon.aqdb.model.metacluster import MetaCluster, MetaClusterMember
from aquilon.aqdb.model.machine_specs import MachineSpecs
