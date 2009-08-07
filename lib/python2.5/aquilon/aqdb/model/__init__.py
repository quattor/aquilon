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

#HARDWARE
from aquilon.aqdb.model.vendor import Vendor
from aquilon.aqdb.model.model import Model
from aquilon.aqdb.model.hardware_entity import HardwareEntity
from aquilon.aqdb.model.cpu import Cpu
from aquilon.aqdb.model.machine import Machine
from aquilon.aqdb.model.disk_type import DiskType
from aquilon.aqdb.model.disk import Disk
from aquilon.aqdb.model.machine_specs import MachineSpecs
from aquilon.aqdb.model.status import Status
from aquilon.aqdb.model.tor_switch_hw import TorSwitchHw
from aquilon.aqdb.model.chassis_hw import ChassisHw
from aquilon.aqdb.model.console_server_hw import ConsoleServerHw


#SYSTEM
from aquilon.aqdb.model.system import System
from aquilon.aqdb.model.chassis import Chassis
from aquilon.aqdb.model.console_server import ConsoleServer
from aquilon.aqdb.model.manager import Manager
from aquilon.aqdb.model.domain import Domain
from aquilon.aqdb.model.host import Host
from aquilon.aqdb.model.build_item import BuildItem
from aquilon.aqdb.model.tor_switch import TorSwitch

#HARDWARE/SYSTEM LINKAGES
from aquilon.aqdb.model.observed_mac import ObservedMac
from aquilon.aqdb.model.serial_cnxn  import SerialCnxn
from aquilon.aqdb.model.chassis_slot import ChassisSlot
from aquilon.aqdb.model.interface    import Interface
from aquilon.aqdb.model.auxiliary import Auxiliary

#SERVICE
from aquilon.aqdb.model.service import Service
from aquilon.aqdb.model.service_instance import ServiceInstance
from aquilon.aqdb.model.service_instance_server import ServiceInstanceServer
from aquilon.aqdb.model.service_map import ServiceMap
from aquilon.aqdb.model.service_list_item import ServiceListItem
from aquilon.aqdb.model.personality_service_map import PersonalityServiceMap
from aquilon.aqdb.model.personality_service_list_item import PersonalityServiceListItem



