# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009-2013,2019  Contributor
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
""" Miscelaneous helper libraries for testing """


import copy
import random
import re
import string

from broker.brokertest import TestBrokerCommand
from broker.machinetest import MachineTestMixin


def import_depends():
    """ Set up the sys.path for loading library dependencies """
    import os
    import sys

    _DIR = os.path.dirname(os.path.realpath(__file__))
    _LIBDIR = os.path.join(_DIR, "..", "..", "lib")
    _TESTDIR = os.path.join(_DIR, "..")

    if _LIBDIR not in sys.path:
        sys.path.insert(0, _LIBDIR)

    if _TESTDIR not in sys.path:
        sys.path.insert(1, _TESTDIR)

    # noinspection PyUnresolvedReferences
    import depends


class MockHubEngine(TestBrokerCommand, MachineTestMixin):
    pass


class MockHub(object):
    # Examples of usage from inside a test defined in an instance of
    # TestBrokerCommand (or its subclass):
    #
    #   If you just need 10 desks (and do not want to worry about creating
    #   cities, buildings etc.):
    #
    #   mh = MockHub(self)  # you should first create a hub
    #   mydesks = mh.add_desks(10)
    #
    #   If you need 5 buildings, and 5 desks in each building:
    #
    #   mh = MockHub(self)  # you should first create a hub
    #   mybuildings = mh.add_buildings(5)
    #   mydesks = {b: mh.add_desks(5, building=b) for b in mybuildings}
    #
    #   Cities, countries, machines etc. can be created analogously to what
    #   is shown in the above examples.  Please see the individual methods
    #   of this class to see what can be achieved and how.
    #
    #   If you want to clean up (i.e. delete the hub with all the buildings,
    #   machines, etc. created for the current test) before other tests are
    #   executed, please use:
    #
    #   mh.delete()
    #
    # This class assumes that the following are true:
    #       - engine implements TestBrokerCommand
    #       - if you provide default_personality, it has to already be in
    #         the 'current' stage (if you do not provide it,
    #         a new personality will be created, and then promoted)
    # Additional requirements if one wants to use machines or hosts:
    #       - the engine class inherits from MachineTestMixin (if it does not,
    #         a shallow copy of the engine will be created, and its class will
    #         be modified to include the missing mixin)
    #       - all dependencies for create_machine_dl360g9 defined (e.g. model)
    def __init__(self, engine, name=None, organisation=None, domain=None,
                 default_archetype=None, default_personality=None,
                 default_os=None, default_os_version=None,
                 grn='grn:/ms/ei/aquilon/aqd'):
        # The engine object should be an instance of TestBrokerCommand (or its
        # subclass), and, if one wants to create machines or hosts,
        # it should include a working method create_machine_dl360g9 (as
        # provided by machinetest.MachineTestMixin).  For the sake of
        # convenience, let us create a new class with the mixin on-the-fly,
        # and use it with a shallow copy of the provided engine object,
        # if the latter does not already include the mixin.
        assert isinstance(engine, TestBrokerCommand)
        if not isinstance(engine, MachineTestMixin):
            # noinspection PyTypeChecker
            self._engine = copy.copy(engine)  # type: MockHubEngine
            self._engine.__class__ = type(
                '{}ModifiedByMockHub'.format(engine.__class__.__name__),
                (engine.__class__, MachineTestMixin), {})
        else:
            # noinspection PyTypeChecker
            self._engine = engine  # type: MockHubEngine
        self._name = None
        self.default_organisation = organisation or self.random_name()
        self.default_domain = domain or self.random_name()
        self.default_archetype = default_archetype or self.random_name()
        self.default_personality = default_personality or self.random_name()
        self.default_os = default_os or self.random_name()
        self.default_os_version = default_os_version or self.random_name()
        self.grn = grn
        self.organisations = []
        self.archetypes = []
        self.personalities = []
        self.operating_systems = []
        self.domains = []
        self.continents = []
        self.countries = []
        self.cities = []
        self.buildings = []
        self.desks = []
        self.machines = {}
        self.hosts = {}
        self.dns_domains = []
        self.networks = {}
        self.create(name)
        self._initialise_dependencies()
        self.default_dns_domain = self.add_dns_domain('{}.cc'.format(
            self._name))

    def get_building(self, machine=None, desk=None):
        building = None
        if machine in self.machines:
            out, _ = self._engine.successtest(['show_machine',
                                               '--machine', machine,
                                               '--format', 'csv'])
            building = out.split(',')[2]
        elif desk in self.desks:
            out, _ = self._engine.successtest(['show_desk',
                                               '--desk', desk,
                                               '--format', 'csv'])
            building = out.split(',')[3]
        return building or None

    def get_default_dns_domain(self, building):
        # Return a default DNS domain for a building.
        result = None
        if building not in self.buildings:
            raise ValueError('Building {} not found.'.format(building))
        out, _ = self._engine.successtest(['show_building',
                                           '--building', building])
        found = re.search(r'Default DNS Domain: (\S+)\s+', out)
        if found:
            result = found.group(1)
        return result

    def get_next_available_hostname(self, prefix, dns_domain):
        prefix_length = len(prefix)
        suffix_length = len(dns_domain) + 1
        index_range = slice(prefix_length, -suffix_length)
        out, _ = self._engine.successtest(['search_host',
                                           '--dns_domain', dns_domain])
        assigned_numbers = [int(l[index_range])
                            for l in out.split() if l.startswith(prefix)]
        next_available = 1
        while next_available in assigned_numbers:
            next_available += 1
        return '{}{}.{}'.format(prefix, next_available, dns_domain)

    def add_dns_domain(self, fqdn):
        if fqdn in self.dns_domains:
            raise ValueError('DNS domain {} already exists.'.format(fqdn))
        self._engine.dsdb_expect('add_dns_domain -domain_name {} '
                                 '-comments '.format(fqdn))
        self._engine.noouttest(['add_dns_domain', '--dns_domain', fqdn,
                                '--restricted',
                                '--justification', 'tcm=123456789'])
        self._engine.dsdb_verify()
        self.dns_domains.append(fqdn)
        return fqdn

    def delete_dns_domain(self, fqdn):
        self._engine.dsdb_expect('delete_dns_domain -domain_name {}'.format(
            fqdn))
        self._engine.noouttest(['del_dns_domain', '--dns_domain', fqdn])
        self._engine.dsdb_verify()
        self.dns_domains.remove(fqdn)
        if fqdn == self.default_dns_domain:
            self.default_dns_domain = None

    def add_network(self, name=None, location_type='hub', location=None):
        name = self.get_or_create_name(name)
        if name in self.networks:
            raise ValueError('Network {} already exists.'.format(name))
        if location_type == 'hub':
            location = self._name
        elif location_type == 'continent':
            location = self.get_or_create_continent(location)
        elif location_type == 'country':
            location = self.get_or_create_country(location)
        elif location_type == 'city':
            location = self.get_or_create_city(location)
        elif location_type == 'building':
            location = self.get_or_create_building(location)
        elif location_type == 'desk':
            location = self.get_or_create_desk(location)
        # If location and type not listed above, we will still try to use them.
        self.networks[name] = {
            'net': self._engine.net.allocate_network(
                testsuite=self._engine, name=name,
                prefixlength=28, network_type='unknown',
                loc_type=location_type, loc_name=location),
            'allocated': set()
        }
        return name

    def delete_network(self, name=None):
        self._engine.net.dispose_network(self._engine, name)
        del self.networks[name]

    def add_archetype(self, name=None):
        name = self.get_or_create_name(name)
        if name in self.archetypes:
            raise ValueError('Archetype {} already exists.'.format(name))
        self._engine.noouttest(['add_archetype', '--archetype', name])
        self.archetypes.append(name)
        return name

    def add_os(self, name, version, archetype):
        os = (name, version, archetype)
        if os in self.operating_systems:
            raise ValueError('OS {} (version {}) for archetype {} already '
                             'exists.'.format(name, version, archetype))
        self._engine.noouttest(['add_os',
                                '--osname', name, '--osversion', version,
                                '--archetype', archetype])
        self.operating_systems.append(os)
        return os

    def add_personality(self, name, archetype, promote=True):
        personality = (name, archetype)
        if personality in self.personalities:
            raise ValueError('Personality {} (archetype: {}) already '
                             'exists.'.format(name, archetype))
        command = ['add_personality',
                   '--personality', name, '--archetype', archetype,
                   '--grn', self.grn, '--config_override',
                   '--host_environment', 'dev']
        self._engine.successtest(command)
        self._engine.check_plenary_exists(
            self.default_archetype,
            'personality', '{}+next'.format(name),
            'config')
        if promote:
            self._engine.successtest(['promote', '--personality', name,
                                      '--archetype', archetype])
        self.personalities.append(personality)
        return personality

    def add_organisation(self, name=None):
        name = self.get_or_create_name(name)
        if name in self.organisations:
            raise ValueError('Organisation {} already exists.'.format(name))
        self._engine.noouttest(['add_organization', '--organization', name])
        self.organisations.append(name)
        return name

    def add_domain(self, name=None):
        name = self.get_or_create_name(name)
        if name in self.domains:
            raise ValueError('Domain {} already exists.'.format(name))
        self._engine.noouttest(['add_domain', '--domain', name]
                               + self._engine.valid_just_tcm)
        self.domains.append(name)
        return name

    @staticmethod
    def random_name(length=8):
        return ''.join(random.choice(string.lowercase) for _ in range(length))

    def _verify_deletion_with_search_hub(self, singular, container):
        search_command = ['search_{}'.format(singular), '--hub', self._name]
        out, _ = self._engine.successtest(search_command)
        found = set(out.split())
        for item in container:
            if item in found:
                raise RuntimeError(
                    'At least one {singular} has not been deleted ('
                    '{singular}: {item})'.format(singular=singular, item=item))

    def delete_hosts(self, slow=False, verify=False):
        # Use slow=True to find hosts for deletion using 'aq search host
        # --hub ...' instead of deleting only hosts defined in self.hosts (i.e.
        # just those created using methods provided by this class).
        search_command = ['search_host', '--hub', self._name]
        if slow:
            out, _ = self._engine.successtest(search_command)
            hosts = out.split()
            ips = []
            for host in hosts:
                out, _ = self._engine.successtest(['show_fqdn', '--fqdn', host,
                                                   '--format', 'csv'])
                ips.append(out.split(',')[3])
        else:
            hosts = self.hosts.keys()
            ips = []
            for host in self.hosts:
                machine = self.hosts[host]['machine']
                net = self.networks[self.machines[machine]['network']]['net']
                ips.append(net.usable[self.machines[machine]['net_index']])
        for i in range(len(hosts)):
            self._engine.dsdb_expect_delete(ip=ips[i])
            self._engine.successtest(['del_host', '--hostname', hosts[i]])
            self._engine.dsdb_verify()
        # Verify if all the hosts in self.hosts have been deleted.
        if verify:
            self._verify_deletion_with_search_hub('host', self.hosts)
        self.hosts = {}

    def delete_machines(self, slow=False, verify=False):
        # Use slow=True to find machines for deletion using 'aq search machine
        # --hub ...' instead of deleting only machines defined in self.machines
        # (i.e. just those created using methods provided by this class).
        search_command = ['search_machine', '--hub', self._name]
        if slow:
            out, _ = self._engine.successtest(search_command)
            machines = out.split()
        else:
            machines = self.machines.keys()
        for machine in machines:
            self._engine.successtest(['del_machine', '--machine', machine])
        # Verify if all the machines in self.machines have been deleted.
        if verify:
            if verify:
                self._verify_deletion_with_search_hub('machine', self.machines)
        self.machines = {}

    def _verify_deletion_with_show_all(self, singular, container, csv_index=1):
        out, _ = self._engine.successtest(['show_{}'.format(singular), '--all',
                                           '--format', 'csv'])
        found = {line.split(',')[csv_index]
                 for line in out.split() if line.count(',') >= csv_index}
        for item in container:
            if item in found:
                raise RuntimeError(
                    'At least one {singular} has not been deleted ({singular}:'
                    ' {item})'.format(singular=singular, item=item))

    def _exists_according_to_show_all(self, singular, name, csv_index=1):
        out, _ = self._engine.successtest(['show_{}'.format(singular), '--all',
                                           '--format', 'csv'])
        found = {line.split(',')[csv_index]
                 for line in out.split() if line.count(',') >= csv_index}
        return name in found

    def _exists_according_to_show(self, singular, name=None, *args):
        command = ['show_{}'.format(singular)]
        if name:
            command.extend(['--{}'.format(singular), name])
        if args:
            command.extend(list(args))
        try:
            _ = self._engine.notfoundtest(command)  # noqa: F841
        except AssertionError:
            return True
        else:
            return False

    def delete_desks(self, verify=False):
        for desk in self.desks:
            self._engine.successtest(['del_desk', '--desk', desk])
        if verify:
            self._verify_deletion_with_show_all('desk', self.desks)
        self.desks = []

    def delete_buildings(self, verify=False):
        for building in self.buildings:
            self._engine.dsdb_expect('delete_building_aq -building {}'.format(
                building))
            self._engine.successtest(['del_building', '--building', building])
            self._engine.dsdb_verify()
        if verify:
            self._verify_deletion_with_show_all('building', self.buildings)
        self.buildings = []

    def delete_cities(self, verify=False):
        for city in self.cities:
            self._engine.dsdb_expect('delete_city_aq -city {}'.format(city))
            self._engine.successtest(['del_city', '--city', city,
                                     '--force_if_orphaned'])
            self._engine.dsdb_verify()
        if verify:
            self._verify_deletion_with_show_all('city', self.cities)
        self.cities = []

    def delete_countries(self, verify=False):
        for country in self.countries:
            self._engine.successtest(['del_country', '--country', country,
                                     '--force_non_empty'])
        if verify:
            self._verify_deletion_with_show_all('country', self.countries)
        self.countries = []

    def delete_continents(self, verify=False):
        for continent in self.continents:
            self._engine.successtest(['del_continent',
                                      '--continent', continent])
        if verify:
            self._verify_deletion_with_show_all('continent', self.continents)
        self.continents = []

    def delete_archetypes(self, verify=False):
        for archetype in self.archetypes:
            self._engine.successtest(['del_archetype',
                                      '--archetype', archetype])
        if verify:
            self._verify_deletion_with_show_all('archetype', self.archetypes)
        self.archetypes = []

    def delete_operating_systems(self, verify=False):
        for os in self.operating_systems:
            osname, osversion, archetype = os
            arguments = ['--osname', osname, '--osversion', osversion,
                         '--archetype', archetype]
            self._engine.successtest(['del_os'] + arguments)
            if verify:
                self._exists_according_to_show('os', None, arguments)
                raise RuntimeError(
                    'At least one OS has not been deleted ({}).'.format(os))
        self.operating_systems = []

    def delete_personalities(self, verify=False):
        for personality in self.personalities:
            name, archetype = personality
            arguments = ['--personality', name,
                         '--archetype', archetype]
            self._engine.successtest(['del_personality'] + arguments)
            if verify:
                self._exists_according_to_show('personality', None, arguments)
                raise RuntimeError('At least one personality has not been '
                                   'deleted ({}).'.format(personality))
        self.personalities = []

    def delete_domains(self, verify=False):
        for domain in self.domains:
            self._engine.successtest(['update_domain', '--domain', domain,
                                      '--archived']
                                     + self._engine.valid_just_tcm)
            self._engine.successtest(['del_domain', '--domain', domain]
                                     + self._engine.valid_just_tcm)
        if verify:
            self._verify_deletion_with_show_all('domain', self.domains)
        self.domains = []

    def delete_organisations(self, verify=False):
        for organisation in self.organisations:
            self._engine.successtest(['del_organization',
                                      '--organization', organisation])
        if verify:
            self._verify_deletion_with_show_all('organization',
                                                self.organisations)
        self.organisations = []

    def delete(self, slow=False, verify=False):
        # Use slow=True to try to delete objects not created via methods
        # defined in this class.
        # Use verify=True to confirm if all objects stored in MockHub have been
        # deleted.
        self.delete_hosts(slow, verify)
        # Delete machines.
        self.delete_machines(slow, verify)
        # Delete desks.
        self.delete_desks(verify)
        # Delete buildings.
        self.delete_buildings(verify)
        # Delete cities.
        self.delete_cities(verify)
        # Delete countries.
        self.delete_countries(verify)
        # Delete continents.
        self.delete_continents(verify)
        # Delete personalities.
        self.delete_personalities(verify)
        # Delete operating systems.
        self.delete_operating_systems(verify)
        # Delete archetypes.
        self.delete_archetypes(verify)
        # Delete domains.
        self.delete_domains(verify)
        # Delete DNS domains.
        for dns_domain in self.dns_domains[:]:
            self.delete_dns_domain(dns_domain)
        if verify:
            self._verify_deletion_with_show_all(
                'dns_domain', self.dns_domains, 0)
        # Delete networks.
        for net in self.networks.keys():
            self.delete_network(net)
        if verify:
            self._verify_deletion_with_show_all(
                'network', self.networks, 0)
        # Last but not least, delete the hub itself, then all the organisations
        # created by the hub, including the organisation to which the hub
        # belongs if the organisation has been created by MockHub.
        if self._name is not None:
            self._engine.noouttest(['del_hub', '--hub', self._name])
            if verify:
                self._verify_deletion_with_show_all(
                    'hub', [self._name], 1)
            self._name = None
        self.delete_organisations(verify)

    def create(self, name=None):
        if self._name is not None:
            raise ValueError('Hub {} already exists.'.format(self._name))
        if name is None:
            name = self.random_name()
        # Add the default organisation if it does not exist.
        if not self._exists_according_to_show('organization',
                                              self.default_organisation):
            self.add_organisation(self.default_organisation)
        command = ['add_hub', '--hub', name,
                   '--organization', self.default_organisation]
        self._engine.noouttest(command)
        self._name = name

    def add_continent(self, name=None):
        name = self.get_or_create_name(name)
        if name in self.continents:
            raise ValueError('Continent {} already exists.'.format(name))
        self._engine.noouttest(['add_continent', '--continent', name,
                               '--hub', self._name])
        self.continents.append(name)
        return name

    def add_continents(self, count=1):
        continents = []
        for i in range(count):
            continents.append(self.add_continent())
        return continents

    def get_or_create_name(self, name=None):
        if name is None:
            name = self.random_name()
        return name

    @staticmethod
    def _get_or_create(container, method, name, **kwargs):
        if container:
            result = name or sorted(container)[0]  # sorted ensures Sequence
        else:
            result = name or method(**kwargs)
        return result if result in container else method(result, **kwargs)

    def get_or_create_dns_domain(self, name, **kwargs):
        return self._get_or_create(self.dns_domains, self.add_dns_domain,
                                   name, **kwargs)

    def get_or_create_network(self, name, **kwargs):
        return self._get_or_create(self.networks, self.add_network,
                                   name, **kwargs)

    def get_or_create_archetype(self, name):
        return self._get_or_create(self.archetypes, self.add_archetype, name)

    def get_or_create_domain(self, name):
        return self._get_or_create(self.domains, self.add_domain, name)

    def get_or_create_continent(self, name):
        return self._get_or_create(self.continents, self.add_continent, name)

    def get_or_create_country(self, name):
        return self._get_or_create(self.countries, self.add_country, name)

    def get_or_create_city(self, name):
        return self._get_or_create(self.cities, self.add_city, name)

    def get_or_create_building(self, name):
        return self._get_or_create(self.buildings, self.add_building, name)

    def get_or_create_desk(self, name, **kwargs):
        return self._get_or_create(self.desks, self.add_desk, name, **kwargs)

    def get_or_create_machine(self, name, **kwargs):
        return self._get_or_create(self.machines, self.add_machine,
                                   name, **kwargs)

    def get_or_create_host(self, name, **kwargs):
        return self._get_or_create(self.hosts, self.add_host,
                                   name, **kwargs)

    def add_country(self, name=None, continent=None):
        name = self.get_or_create_name(name)
        if name in self.countries:
            raise ValueError('Country {} already exists.'.format(name))
        continent = self.get_or_create_continent(continent)
        self._engine.noouttest(['add_country', '--country', name,
                               '--continent', continent])
        self.countries.append(name)
        return name

    def add_countries(self, count=1, continent=None):
        continent = self.get_or_create_continent(continent)
        countries = []
        for i in range(count):
            countries.append(self.add_country(continent=continent))
        return countries

    def add_city(self, name=None, country=None):
        name = self.get_or_create_name(name)
        if name in self.cities:
            raise ValueError('City {} already exists.'.format(name))
        country = self.get_or_create_country(country)
        self._engine.dsdb_expect('add_city_aq -city_symbol {name} '
                                 '-country_symbol {country} '
                                 '-city_name {name}'.format(name=name,
                                                            country=country))
        self._engine.noouttest(['add_city', '--city', name, '--fullname', name,
                                '--timezone', 'Europe/Warsaw',
                                '--country', country])
        self._engine.dsdb_verify()
        self.cities.append(name)
        return name

    def add_cities(self, count=1, country=None):
        country = self.get_or_create_country(country)
        cities = []
        for i in range(count):
            cities.append(self.add_city(country=country))
        return cities

    def add_building(self, name=None, city=None):
        name = self.get_or_create_name(name)
        if name in self.buildings:
            raise ValueError('Building {} already exists.'.format(name))
        address = '{}address'.format(name)
        city = self.get_or_create_city(city)
        self._engine.dsdb_expect(
            'add_building_aq -building_name {name} -city {city} -building_addr'
            ' {address}'.format(name=name, city=city, address=address))
        self._engine.noouttest(['add_building', '--building', name,
                                '--address', '{}'.format(address),
                                '--city', city])
        self._engine.dsdb_verify()
        self.buildings.append(name)
        return name

    def add_buildings(self, count=1, city=None):
        city = self.get_or_create_city(city)
        buildings = []
        for i in range(count):
            buildings.append(self.add_building(city=city))
        return buildings

    def add_desk(self, name=None, building=None):
        name = self.get_or_create_name(name)
        if name in self.desks:
            raise ValueError('Desk {} already exists.'.format(name))
        building = self.get_or_create_building(building)
        self._engine.noouttest(['add_desk', '--desk', name,
                               '--building', building])
        self.desks.append(name)
        return name

    def add_desks(self, count=1, building=None):
        building = self.get_or_create_building(building)
        desks = []
        for i in range(count):
            desks.append(self.add_desk(building=building))
        return desks

    def add_machine(self, name=None, desk=None, building=None,
                    network=None, net_index=None, net_index_limit=10**5):
        name = self.get_or_create_name(name)
        if name in self.machines:
            raise ValueError('Machine {} already exists.'.format(name))
        # The following does create a new desk in the given building but does
        # not ensure that a pre-existing desk is contained in the given
        # building.
        desk = self.get_or_create_desk(desk, building=building)
        network_kwargs = {}
        if building:
            network_kwargs = {'location_type': 'building',
                              'location': building}
        network = self.get_or_create_network(network, **network_kwargs)
        net = self.networks[network]
        if net_index is None:
            # Find next available network index.
            for i in range(net_index_limit):
                if i not in net['allocated']:
                    net_index = i
                    # Mark index as allocated and exit.
                    net['allocated'].add(net_index)
                    break
            else:
                raise ValueError(
                    'Network index limit of {limit} reached.  Could not find '
                    'unallocated network index on network {network}.'.format(
                        limit=net_index_limit, network=network))
        # Get MAC or raise an error if found net index out of range.
        eth0_mac = net['net'].usable[net_index].mac
        self._engine.create_machine_dl360g9(name, desk=desk, eth0_mac=eth0_mac)
        self.machines[name] = {'network': network, 'net_index': net_index,
                               'desk': desk, 'building': building}
        return name

    def add_machines(self, count=1, desk=None, building=None, network=None):
        # Create 'count' machines assigned to 'desk' in 'building' (but please
        # see below), and connected to 'network' (located in 'building' if
        # 'building' given).
        # The following does create a new desk in the given building but does
        # not ensure that a pre-existing desk is contained in the given
        # building.
        desk = self.get_or_create_desk(desk, building=building)
        network_kwargs = {}
        if building:
            network_kwargs = {'location_type': 'building',
                              'location': building}
        network = self.get_or_create_network(network, **network_kwargs)
        machines = []
        for i in range(count):
            machines.append(self.add_machine(desk=desk, network=network))
        return machines

    def add_host(self, hostname=None,
                 prefix=None, dns_domain=None,
                 machine=None, building=None, desk=None):
        # If machine does not exist, and desk exists, building is ignored.
        # If hostname given, prefix and dns_domain are ignored.
        # NB: Hosts stored in self.hosts by hostname (given directly or
        # computed) which has to be unique.
        if hostname and (prefix or dns_domain):
            raise ValueError(
                'Prefix or DNS domain cannot be used when hostname ({}) '
                'already given.'.format(hostname))
        if not (hostname or prefix):
            name = prefix = self.random_name()
        elif hostname:
            name = hostname.lower().strip().split('.')[0]
        else:
            name = prefix.lower().strip()
        if name in self.hosts:
            raise ValueError('Host {} already exists.'.format(name))

        if machine:
            machine = self.get_or_create_machine(machine,
                                                 desk=desk, building=building)
        else:
            machine = self.add_machine(desk=desk, building=building)
        if building and building != self.machines[machine]['building']:
            raise ValueError(
                'Machine {machine} is located in building {machine_building} '
                'instead of building {requested_building}.'.format(
                    machine=machine,
                    machine_building=self.machines[machine]['building'],
                    requested_building=building))
        if desk and desk != self.machines[machine]['desk']:
            raise ValueError(
                'Machine {machine} is assigned to desk {machine_desk} '
                'instead of desk {requested_desk}.'.format(
                    machine=machine,
                    machine_desk=self.machines[machine]['desk'],
                    requested_desk=desk))

        net = self.networks[self.machines[machine]['network']]['net']
        ip = net.usable[self.machines[machine]['net_index']]
        mac = net.usable[self.machines[machine]['net_index']].mac
        command = ['add_host', '--domain', self.default_domain,
                   '--archetype', self.default_archetype,
                   '--personality', self.default_personality,
                   '--osname', self.default_os,
                   '--osversion', self.default_os_version,
                   '--ip', ip, '--machine', machine]
        if hostname:
            command.extend(['--hostname', hostname])
        else:
            command.extend(['--prefix', prefix])
            # If no hostname, building, desk and dns_domain given, attempt to
            # create the host in self.default_dns_domain.
            if not (building or desk or dns_domain):
                dns_domain = self.default_dns_domain
            if dns_domain:
                command.extend(['--dns_domain', dns_domain])
            else:
                dns_domain = self.get_default_dns_domain(self.get_building(
                    machine))
            if not dns_domain:
                raise ValueError(
                    'Could not find default DNS domain while attempting to add'
                    ' a host with prefix {}.'.format(prefix))
            hostname = self.get_next_available_hostname(prefix, dns_domain)
        self._engine.dsdb_expect_add(hostname, ip, 'eth0', mac)
        self._engine.successtest(command)
        self._engine.dsdb_verify()
        self.hosts[hostname] = {'machine': machine, 'dns_domain': dns_domain,
                                'building': building, 'desk': desk}
        return name

    def add_hosts(self, count=1, prefix=None, dns_domain=None,
                  building=None, desk=None, machines=None):
        # Create 'count' hosts using a given prefix (and 'dns_domain' if given
        #  -- otherwise the default DNS domain for a given building,
        # desk or machine will be used where available,
        # and self.default_dns_domain in other cases).
        # If 'prefix' not given, generate a random prefix.
        # If a list of machines is not given, create new machines assigned
        # to 'desk' or a new desk created in 'building'.  Otherwise,
        # use machines from the given list.  If the list of machines is
        # shorter than 'count', use the machines from the list, and create
        # additional machines as needed.
        if not machines or len(machines) < count:
            desk = self.get_or_create_desk(desk, building=building)
        default_dns_domain = dns_domain or self.default_dns_domain
        if desk:
            default_dns_domain = (
                    dns_domain
                    or self.get_default_dns_domain(self.get_building(
                                                                    desk=desk))
                    or self.default_dns_domain)
        prefix = self.get_or_create_name(prefix)
        hosts = []
        for i in range(count):
            machine = None
            if machines and i < len(machines):
                machine = self.get_or_create_machine(machines[i])
            elif machines:
                machine = self.get_or_create_machine(name=None, desk=desk)
            if machine:
                dns = (dns_domain
                       or self.get_default_dns_domain(self.get_building(
                            machine))
                       or default_dns_domain)
                hosts.append(
                    self.add_host(prefix=prefix, dns_domain=dns,
                                  machine=machine))
            else:
                hosts.append(
                    self.add_host(prefix=prefix, dns_domain=default_dns_domain,
                                  desk=desk))
        return hosts

    def _initialise_dependencies(self):
        # Add the default domain if it does not exist.
        if not self._exists_according_to_show('domain', self.default_domain):
            self.add_domain(self.default_domain)
        # Add the default archetype if it does not exist.
        if not self._exists_according_to_show_all('archetype',
                                                  self.default_archetype):
            self.add_archetype(self.default_archetype)
        # Add the default OS if it does not exist.
        os = ['--osname', self.default_os,
              '--osversion', self.default_os_version,
              '--archetype', self.archetypes]
        if not self._exists_according_to_show('os', None, *os):
            self.add_os(self.default_os, self.default_os_version,
                        self.default_archetype)
        # Add the default personality for the default archetype if it does not
        # exist.
        personality = ['--personality', self.default_personality,
                       '--archetype', self.default_archetype]
        if not self._exists_according_to_show(
                'personality', None, *personality):
            self.add_personality(self.default_personality,
                                 self.default_archetype)
