# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2013  Contributor
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
from aquilon.aqdb.model.base import Base

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
from aquilon.aqdb.model.campus import Campus
from aquilon.aqdb.model.rack import Rack
from aquilon.aqdb.model.desk import Desk
from aquilon.aqdb.model.location_search_list import LocationSearchList
from aquilon.aqdb.model.search_list_item import SearchListItem

#NETWORK
from aquilon.aqdb.model.network import Network
from aquilon.aqdb.model.dns_domain import DnsDomain

#CONFIG
from aquilon.aqdb.model.tld import Tld
from aquilon.aqdb.model.cfg_path import CfgPath
from aquilon.aqdb.model.archetype import Archetype
from aquilon.aqdb.model.personality import Personality
from aquilon.aqdb.model.operating_system import OperatingSystem

#HARDWARE
from aquilon.aqdb.model.vendor import Vendor
from aquilon.aqdb.model.model import Model
from aquilon.aqdb.model.hardware_entity import HardwareEntity
from aquilon.aqdb.model.cpu import Cpu
from aquilon.aqdb.model.machine import Machine
from aquilon.aqdb.model.status import Status
from aquilon.aqdb.model.tor_switch_hw import TorSwitchHw
from aquilon.aqdb.model.chassis_hw import ChassisHw
from aquilon.aqdb.model.console_server_hw import ConsoleServerHw

#SYSTEM
from aquilon.aqdb.model.system import System, DynamicStub
from aquilon.aqdb.model.chassis import Chassis
from aquilon.aqdb.model.console_server import ConsoleServer
from aquilon.aqdb.model.manager import Manager
from aquilon.aqdb.model.domain import Domain
from aquilon.aqdb.model.host import Host
from aquilon.aqdb.model.tor_switch import TorSwitch

#HARDWARE/SYSTEM LINKAGES
from aquilon.aqdb.model.observed_mac import ObservedMac
from aquilon.aqdb.model.serial_cnxn  import SerialCnxn
from aquilon.aqdb.model.chassis_slot import ChassisSlot
from aquilon.aqdb.model.interface import Interface
from aquilon.aqdb.model.auxiliary import Auxiliary

#SERVICE
from aquilon.aqdb.model.service import Service
from aquilon.aqdb.model.service_instance import ServiceInstance
from aquilon.aqdb.model.service_instance_server import ServiceInstanceServer
from aquilon.aqdb.model.service_map import ServiceMap
from aquilon.aqdb.model.service_list_item import ServiceListItem
from aquilon.aqdb.model.personality_service_map import PersonalityServiceMap
from aquilon.aqdb.model.personality_service_list_item import PersonalityServiceListItem

#NasDisk depends on ServiceInstance
from aquilon.aqdb.model.disk import Disk, LocalDisk, NasDisk

#CLUSTER
from aquilon.aqdb.model.cluster import (Cluster, EsxCluster,
                                        HostClusterMember,
                                        MachineClusterMember,
                                        ClusterAlignedService,
                                        ClusterServiceBinding)

from aquilon.aqdb.model.metacluster import MetaCluster, MetaClusterMember
from aquilon.aqdb.model.machine_specs import MachineSpecs

#build items link to service instances
from aquilon.aqdb.model.build_item import BuildItem
