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
from base import Base

#AUTHORIZATION
from role import Role
from realm import Realm
from user_principal import UserPrincipal

#LOCATION
from location import Location
from company import Company
from hub import Hub
from continent import Continent
from country import Country
from city import City
from building import Building
from campus import Campus
from rack import Rack
from desk import Desk
from location_search_list import LocationSearchList
from search_list_item import SearchListItem

#NETWORK
from network import Network
from dns_domain import DnsDomain

#CONFIG
from tld import Tld
from cfg_path import CfgPath
from archetype import Archetype
from personality import Personality
from operating_system import OperatingSystem

#HARDWARE
from vendor import Vendor
from model import Model
from hardware_entity import HardwareEntity
from cpu import Cpu
from machine import Machine
from status import Status
from tor_switch_hw import TorSwitchHw
from chassis_hw import ChassisHw
from console_server_hw import ConsoleServerHw

#SYSTEM
from system import System, DynamicStub
from chassis import Chassis
from console_server import ConsoleServer
from manager import Manager
from domain import Domain
from host import Host
from tor_switch import TorSwitch

#HARDWARE/SYSTEM LINKAGES
from observed_mac import ObservedMac
from serial_cnxn  import SerialCnxn
from chassis_slot import ChassisSlot
from interface import Interface
from auxiliary import Auxiliary

#SERVICE
from service import Service
from service_instance import ServiceInstance
from service_instance_server import ServiceInstanceServer
from service_map import ServiceMap
from service_list_item import ServiceListItem
from personality_service_map import PersonalityServiceMap
from personality_service_list_item import PersonalityServiceListItem

#NasDisk depends on ServiceInstance
from disk import Disk, LocalDisk, NasDisk

#CLUSTER
from cluster import (Cluster, EsxCluster,
                                        HostClusterMember,
                                        MachineClusterMember,
                                        ClusterAlignedService,
                                        ClusterServiceBinding)

from metacluster import MetaCluster, MetaClusterMember
from machine_specs import MachineSpecs

#build items link to service instances
from build_item import BuildItem
