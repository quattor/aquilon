# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
import warnings

import aquilon.aqdb.depends
from sqlalchemy.exc import SAWarning

from aquilon.aqdb.model.base import Base
from aquilon.aqdb.model.stateengine import StateEngine

#AUTHORIZATION
from aquilon.aqdb.model.role import Role
from aquilon.aqdb.model.realm import Realm
from aquilon.aqdb.model.user_principal import UserPrincipal

#DNS DOMAINS
from aquilon.aqdb.model.dns_domain import DnsDomain

#LOCATION
from aquilon.aqdb.model.location import Location
from aquilon.aqdb.model.company import Company
from aquilon.aqdb.model.hub import Hub
from aquilon.aqdb.model.continent import Continent
from aquilon.aqdb.model.country import Country
from aquilon.aqdb.model.city import City
from aquilon.aqdb.model.building import Building
from aquilon.aqdb.model.bunker import Bunker
from aquilon.aqdb.model.room import Room
from aquilon.aqdb.model.campus import Campus
from aquilon.aqdb.model.rack import Rack
from aquilon.aqdb.model.desk import Desk

#NETWORK
from aquilon.aqdb.model.dns_environment import DnsEnvironment
from aquilon.aqdb.model.network_environment import NetworkEnvironment
from aquilon.aqdb.model.network import Network
from aquilon.aqdb.model.static_route import StaticRoute
from aquilon.aqdb.model.dns_map import DnsMap
from aquilon.aqdb.model.fqdn import Fqdn
from aquilon.aqdb.model.dns_record import DnsRecord
from aquilon.aqdb.model.a_record import ARecord, DynamicStub
from aquilon.aqdb.model.reserved_name import ReservedName
from aquilon.aqdb.model.alias import Alias
from aquilon.aqdb.model.srv_record import SrvRecord
from aquilon.aqdb.model.ns_record import NsRecord
from aquilon.aqdb.model.router_address import RouterAddress

#CONFIG
from aquilon.aqdb.model.grn import Grn
from aquilon.aqdb.model.archetype import Archetype
from aquilon.aqdb.model.host_environment import HostEnvironment
from aquilon.aqdb.model.personality import Personality, PersonalityGrnMap
from aquilon.aqdb.model.operating_system import OperatingSystem

#HARDWARE
from aquilon.aqdb.model.vendor import Vendor
from aquilon.aqdb.model.model import Model
from aquilon.aqdb.model.hardware_entity import HardwareEntity
from aquilon.aqdb.model.cpu import Cpu
from aquilon.aqdb.model.machine import Machine
from aquilon.aqdb.model.hostlifecycle import HostLifecycle
from aquilon.aqdb.model.switch import Switch
from aquilon.aqdb.model.chassis import Chassis

#HOST
from aquilon.aqdb.model.branch import Branch, Domain, Sandbox
from aquilon.aqdb.model.host import Host, HostGrnMap

#HARDWARE/SYSTEM LINKAGES
from aquilon.aqdb.model.observed_mac import ObservedMac
from aquilon.aqdb.model.chassis_slot import ChassisSlot
from aquilon.aqdb.model.vlan import ObservedVlan, VlanInfo
from aquilon.aqdb.model.interface import (Interface, PublicInterface,
                                          ManagementInterface, OnboardInterface,
                                          VlanInterface, BondingInterface,
                                          BridgeInterface, LoopbackInterface)
from aquilon.aqdb.model.address_assignment import AddressAssignment

#FEATURES
from aquilon.aqdb.model.feature import (Feature, FeatureLink, HostFeature,
                                        HardwareFeature, InterfaceFeature)
from aquilon.aqdb.model.parameter_definition import (ParamDefinition, ParamDefHolder,
                                                     ArchetypeParamDef, FeatureParamDef)
from aquilon.aqdb.model.parameter import (Parameter, ParameterHolder,
                                          PersonalityParameter, FeatureLinkParameter)

#SERVICE
from aquilon.aqdb.model.service import Service
from aquilon.aqdb.model.service_instance import ServiceInstance
from aquilon.aqdb.model.service_instance_server import ServiceInstanceServer
from aquilon.aqdb.model.service_map import ServiceMap
from aquilon.aqdb.model.personality_service_map import PersonalityServiceMap

from aquilon.aqdb.model.disk import Disk, LocalDisk

#CLUSTER
#FIXME: this is a measure to dodge a warning raised by conflicting class names
#in this and hostlifecycle. It's only used for one of the two classes using a
#'with' clause to ensure as few warnings as possible are masked.
#TODO: overhaul this using importlib. Before loading conflicting classes check
# if they already exist in the current 'locals().keys()' and raise some kind of
# error or warning.
#(daqscott 29/10/10)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SAWarning)
    from aquilon.aqdb.model.clusterlifecycle import ClusterLifecycle


from aquilon.aqdb.model.cluster import (Cluster, EsxCluster,
                                        ComputeCluster, StorageCluster)
from aquilon.aqdb.model.personality_cluster_info import (PersonalityClusterInfo,
                                                         PersonalityESXClusterInfo)

from aquilon.aqdb.model.metacluster import MetaCluster, MetaClusterMember
from aquilon.aqdb.model.machine_specs import MachineSpecs

from aquilon.aqdb.model.xtn import Xtn, XtnDetail, XtnEnd

# Resources
from aquilon.aqdb.model.resource import (Resource, ResourceHolder,
                                         HostResource, ClusterResource)
from aquilon.aqdb.model.filesystem import Filesystem
from aquilon.aqdb.model.application import Application
from aquilon.aqdb.model.hostlink import Hostlink
from aquilon.aqdb.model.intervention import Intervention
from aquilon.aqdb.model.resourcegroup import ResourceGroup, BundleResource
from aquilon.aqdb.model.reboot_schedule import (RebootSchedule,
                                                RebootIntervention)

from aquilon.aqdb.model.virtual_machine import VirtualMachine
from aquilon.aqdb.model.service_address import ServiceAddress
from aquilon.aqdb.model.share import Share
from aquilon.aqdb.model.virtual_disk import VirtualDisk
