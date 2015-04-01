# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Wrappers to make getting and using hosts simpler."""

from collections import defaultdict
from six import itervalues
from types import ListType

from sqlalchemy.orm import (joinedload, contains_eager, with_polymorphic,
                            undefer)
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import (HardwareEntity, DnsEnvironment, DnsDomain, Fqdn,
                                DnsRecord, ARecord, ReservedName, Sandbox, Host,
                                HostGrnMap, OperatingSystem, HostLifecycle,
                                Personality, Domain, Machine, NetworkDevice,
                                Disk, ChassisSlot, VirtualMachine)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.feature import (model_features,
                                               personality_features,
                                               check_feature_template)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.templates import (Plenary, PlenaryServiceInstanceServer)
from aquilon.utils import chunk


def create_host(session, logger, config, dbhw, dbarchetype, domain=None,
                sandbox=None, buildstatus=None, personality=None,
                osname=None, osversion=None, grn=None, eon_id=None,
                comments=None, **kwargs):
    # Section in the config used to determin defaults for this archetype
    section = "archetype_" + dbarchetype.name

    # Pick a default domain if not specified or impled by the sandbox
    if not domain and not sandbox and \
       config.has_option(section, "default_domain"):
        domain = config.get(section, "default_domain")

    dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                               sandbox=sandbox, compel=True)

    # Check if the branch allows hosts to be managed
    if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
        raise ArgumentError("Adding hosts to {0:l} is not allowed."
                            .format(dbbranch))

    if not buildstatus:
        buildstatus = 'build'

    dbstatus = HostLifecycle.get_instance(session, buildstatus)

    if not personality:
        if config.has_option(section, "default_personality"):
            personality = config.get(section, "default_personality")
    if not personality:
        raise ArgumentError("There is no default personality configured "
                            "for {0:l}, please specify --personality."
                            .format(dbarchetype))

    dbpersonality = Personality.get_unique(session, name=personality,
                                           archetype=dbarchetype,
                                           compel=True)

    if isinstance(dbbranch, Domain):
        pre, post = personality_features(dbpersonality)
        hw_features = model_features(dbhw.model, dbarchetype, dbpersonality)
        for dbfeature in pre | post | hw_features:
            check_feature_template(config, dbarchetype, dbfeature, dbbranch)

    if not osname:
        if config.has_option(section, "default_osname"):
            osname = config.get(section, "default_osname")

    if not osversion:
        if config.has_option(section, "default_osversion"):
            osversion = config.get(section, "default_osversion")

    if not osname or not osversion:
        raise ArgumentError("Can not determine a sensible default OS "
                            "for archetype %s. Please use the "
                            "--osname and --osversion parameters." %
                            (dbarchetype.name))

    dbos = OperatingSystem.get_unique(session, name=osname,
                                      version=osversion,
                                      archetype=dbarchetype, compel=True)

    dbgrn = None
    if grn or eon_id:
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=config)

    dbhost = Host(hardware_entity=dbhw, branch=dbbranch,
                  owner_grn=dbgrn, sandbox_author=dbauthor,
                  personality=dbpersonality, status=dbstatus,
                  operating_system=dbos, comments=comments)
    session.add(dbhost)

    if dbgrn and config.has_option(section, "default_grn_target"):
        target = config.get(section, "default_grn_target")
        dbhost.grns.append(HostGrnMap(grn=dbgrn, target=target))

    return dbhost


def remove_host(logger, dbhw, plenaries, remove_plenaries):
    if not dbhw.host:
        raise NotFoundException("Hardware entity %s has no host." % dbhw.label)
    dbhost = dbhw.host

    dbhost.lock_row()

    remove_plenaries.append(Plenary.get_plenary(dbhost))

    check_no_provided_service(dbhost)

    for si in dbhost.services_used:
        plenaries.append(PlenaryServiceInstanceServer.get_plenary(si))
        logger.info("Before deleting {0:l}, removing binding to {1:l}"
                    .format(dbhost, si))

    del dbhost.services_used[:]

    if dbhost.resholder:
        for res in dbhost.resholder.resources:
            remove_plenaries.append(Plenary.get_plenary(res))

    if dbhost.cluster:
        dbcluster = dbhost.cluster
        dbcluster.hosts.remove(dbhost)
        set_committed_value(dbhost, '_cluster', None)
        dbcluster.validate()
        plenaries.append(Plenary.get_plenary(dbcluster))

    dbhw.host = None


def hostname_to_host(session, hostname, query_options=None):
    # When the user asked for a host, returning "machine not found" does not
    # feel to be the right error message, even if it is technically correct.
    # It's a little tricky though: we don't want to suppress "dns domain not
    # found"
    parse_fqdn(session, hostname)
    try:
        if not query_options:
            query_options = [joinedload('host'),
                             undefer('host.comments')]
        dbmachine = HardwareEntity.get_unique(session, hostname, compel=True,
                                              query_options=query_options)
    except NotFoundException:
        raise NotFoundException("Host %s not found." % hostname)

    if not dbmachine.host:
        raise NotFoundException("{0} does not have a host "
                                "assigned.".format(dbmachine))
    set_committed_value(dbmachine.host, 'hardware_entity', dbmachine)
    return dbmachine.host


def hostlist_to_hosts(session, hostlist, query_options=None,
                      error=ArgumentError):
    dbdns_env = DnsEnvironment.get_unique_or_default(session)

    failed = []
    parsed_fqdns = defaultdict(list)
    dns_domains = {}
    dns_records_by_name = {}
    dns_records_by_id = {}

    hostlist = [AqStr.normalize(host) for host in hostlist]

    def parse_fqdns():
        for host in hostlist:
            if "." not in host:
                failed.append("%s: Not an FQDN." % host)
                continue
            short, dns_domain = host.split(".", 1)
            parsed_fqdns[dns_domain].append(short)

    def look_up_dns_domains():
        q = session.query(DnsDomain)
        q = q.filter(DnsDomain.name.in_(parsed_fqdns))
        for dbdns_domain in q:
            dns_domains[dbdns_domain.name] = dbdns_domain

        missing = set(parsed_fqdns)
        missing.difference_update(dns_domains)
        for item in missing:
            failed.append("DNS Domain %s not found." % item)

    def look_up_dns_records():
        for dbdns_domain in itervalues(dns_domains):
            short_names = parsed_fqdns[dbdns_domain.name]
            for name_chunk in chunk(short_names, 1000):
                q = session.query(DnsRecord)
                q = q.with_polymorphic([ARecord, ReservedName])
                q = q.join(Fqdn, DnsRecord.fqdn_id == Fqdn.id)
                q = q.filter_by(dns_environment=dbdns_env, dns_domain=dbdns_domain)
                q = q.filter(Fqdn.name.in_(name_chunk))
                q = q.options(contains_eager('fqdn'))
                for dbdns_rec in q:
                    set_committed_value(dbdns_rec.fqdn, 'dns_domain', dbdns_domain)
                    dns_records_by_name[str(dbdns_rec.fqdn)] = dbdns_rec
                    dns_records_by_id[dbdns_rec.id] = dbdns_rec

        missing = set(hostlist)
        missing.difference_update(dns_records_by_name)
        for item in missing:
            failed.append("Host %s not found." % item)

    def look_up_hosts():
        hosts_by_fqdn = {}
        for dns_rec_chunk in chunk(dns_records_by_name.values(), 1000):
            q = session.query(Host)
            HWAlias = with_polymorphic(HardwareEntity, [Machine, NetworkDevice])
            q = q.join(HWAlias)
            q = q.filter(HWAlias.primary_name_id.in_(rec.id for rec in
                                                     dns_rec_chunk))
            q = q.options(contains_eager(Host.hardware_entity.of_type(HWAlias)))
            if query_options:
                q = q.options(*query_options)

            for dbhost in q:
                primary_name = dns_records_by_id[dbhost.hardware_entity.primary_name_id]
                set_committed_value(dbhost.hardware_entity, 'primary_name',
                                    primary_name)
                hosts_by_fqdn[str(primary_name.fqdn)] = dbhost

        # Don't report bad hostnames twice - start from dns_records_by_name
        # rather than from hostlist
        missing = set(dns_records_by_name)
        missing.difference_update(hosts_by_fqdn)
        for item in missing:
            failed.append("Host %s not found." % item)

        return hosts_by_fqdn.values()

    parse_fqdns()
    look_up_dns_domains()
    look_up_dns_records()
    dbhosts = look_up_hosts()

    if error:
        if failed:
            raise error("Invalid hosts in list:\n%s" % "\n".join(failed))
        if not dbhosts:
            raise error("Empty list.")
    return dbhosts


def preload_machine_data(session, dbhosts):
    hw_by_id = {}
    for dbhost in dbhosts:
        hw_by_id[dbhost.hardware_entity.id] = dbhost.hardware_entity

    # Not all hosts are bound to machines, so load the machine-specific
    # attributes separately
    machines = [dbhost.hardware_entity.id for dbhost in dbhosts if
                dbhost.hardware_entity.model.model_type.isMachineType()]
    for machine_chunk in chunk(machines, 1000):
        disks_by_hw = defaultdict(ListType)
        q = session.query(Disk)
        q = q.options(undefer('comments'))
        q = q.filter(Disk.machine_id.in_(machine_chunk))
        for dbdisk in q:
            dbhw = hw_by_id[dbdisk.machine_id]
            set_committed_value(dbdisk, "machine", dbhw)
            disks_by_hw[dbdisk.machine_id].append(dbdisk)

        for hw_id in machine_chunk:
            dbhw = hw_by_id[hw_id]
            if hw_id in disks_by_hw:
                set_committed_value(dbhw, "disks", disks_by_hw[hw_id])
            else:
                set_committed_value(dbhw, "disks", [])

        slots_by_hw = defaultdict(ListType)
        q = session.query(ChassisSlot)
        q = q.filter(ChassisSlot.machine_id.in_(machine_chunk))
        for dbslot in q:
            dbhw = hw_by_id[dbslot.machine_id]
            set_committed_value(dbslot, "machine", dbhw)
            slots_by_hw[dbslot.machine_id].append(dbslot)

        for hw_id in machine_chunk:
            dbhw = hw_by_id[hw_id]
            if hw_id in slots_by_hw:
                set_committed_value(dbhw, "chassis_slot", slots_by_hw[hw_id])
            else:
                set_committed_value(dbhw, "chassis_slot", [])

        vms = set()
        q = session.query(VirtualMachine)
        q = q.filter(VirtualMachine.machine_id.in_(machine_chunk))
        for vm in q:
            dbhw = hw_by_id[vm.machine_id]
            set_committed_value(vm, "machine", dbhw)
            set_committed_value(dbhw, "vm_container", vm)
            vms.add(vm.machine_id)

        for hw_id in set(machine_chunk) - vms:
            dbhw = hw_by_id[hw_id]
            set_committed_value(dbhw, "vm_container", None)


def check_hostlist_size(command, config, hostlist):

    if not hostlist:
        return

    default_max_size = config.getint("broker", "default_max_list_size")
    max_size_opt = "%s_max_list_size" % command
    if config.has_option("broker", max_size_opt):
        if config.get("broker", max_size_opt) != '':
            hostlist_max_size = config.getint("broker", max_size_opt)
        else:
            hostlist_max_size = 0
    else:
        hostlist_max_size = default_max_size

    if not hostlist_max_size:
        return

    if len(hostlist) > hostlist_max_size:
        raise ArgumentError("The number of hosts in list {0:d} can not be "
                            "more than {1:d}".format(len(hostlist), hostlist_max_size))
    return


def validate_branch_author(dbhosts):
    branches = defaultdict(ListType)
    authors = defaultdict(ListType)
    for dbhost in dbhosts:
        branches[(dbhost.branch, dbhost.sandbox_author)].append(dbhost)
        authors[dbhost.sandbox_author].append(dbhost)

    if len(branches) > 1:
        stats = []
        for branch, sandbox_author in sorted(branches,
                                             key=lambda x: -len(branches[x])):
            cnt = len(branches[(branch, sandbox_author)])
            if isinstance(branch, Sandbox):
                stats.append("%d hosts in sandbox %s/%s" %
                             (cnt, sandbox_author, branch))
            else:
                stats.append("{0:d} hosts in {1:l}".format(cnt, branch))
        raise ArgumentError("All hosts must be in the same domain or "
                            "sandbox:\n%s" % "\n".join(stats))
    if len(authors) > 1:
        keys = sorted(authors, key=lambda x: len(authors[x]))
        stats = ["%s hosts with sandbox author %s" %
                 (len(authors[author]), author.name) for author in keys]
        raise ArgumentError("All hosts must be managed by the same "
                            "sandbox author:\n%s" % "\n".join(stats))

    return (branches.popitem()[0][0], authors.popitem()[0])
