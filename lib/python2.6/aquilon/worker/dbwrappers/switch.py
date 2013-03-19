# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Helper functions for managing switches """


import re

from json import JSONDecoder
from random import choice
from ipaddr import IPv4Address
from pipes import quote
from operator import attrgetter

from aquilon.exceptions_ import (InternalError, NotFoundException,
                                 ProcessException, ArgumentError)
from aquilon.aqdb.model import (Service, ServiceInstance, NetworkEnvironment,
                                AddressAssignment, ARecord, Model,
                                RouterAddress)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.processes import run_command
from aquilon.worker.dbwrappers.dns import delete_dns_record, grab_address
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 assign_address,
                                                 rename_interface)
from aquilon.utils import first_of


def determine_helper_hostname(session, logger, config, dbswitch):
    """Try to figure out a useful helper from the mappings.
    """
    helper_name = config.get("broker", "poll_helper_service")
    if not helper_name:  # pragma: no cover
        return
    helper_service = Service.get_unique(session, helper_name,
                                        compel=InternalError)
    mapped_instances = ServiceInstance.get_mapped_instance_cache(
        dbpersonality=None, dblocation=dbswitch.location,
        dbservices=[helper_service])
    for dbsi in mapped_instances.get(helper_service, []):
        if dbsi.server_hosts:
            # Poor man's load balancing...
            jump = choice(dbsi.server_hosts).fqdn
            logger.client_info("Using jump host {0} from {1:l} to run CheckNet "
                               "for {2:l}.".format(jump, dbsi, dbswitch))
            return jump

    logger.client_info("No jump host for %s, calling CheckNet from %s." %
                       (dbswitch, config.get("broker", "hostname")))
    return None


def determine_helper_args(config):
    ssh_command = config.get("broker", "poll_ssh").strip()
    if not ssh_command:  # pragma: no cover
        return []
    ssh_args = [ssh_command]
    ssh_options = config.get("broker", "poll_ssh_options")
    ssh_args.extend(ssh_options.strip().split())
    return ssh_args


def discover_switch(session, logger, config, dbswitch, dryrun):
    """
    Perform switch discovery

    This function can operate in two modes:

    - If dryrun is False, it performs all the operations required to bring the
      definition of the switch in AQDB in line with the discovered status in
      one transaction.

    - If dryrun is True, it returns the list of individual "aq" commands the
      user should execute to get the switch into the desired state.

    In order to make the core logic less complex, simple actions like
    adding/deleting IP addresses and interfaces are implemented as helper
    functions, and those helper functions hide the differences between the
    normal and dryrun modes from the rest of the code.
    """

    importer = config.get("broker", "switch_discover")

    results = []

    dbnet_env = NetworkEnvironment.get_unique_or_default(session)

    def aqcmd(cmd, *args):
        """ Helper function to print an AQ command to be executed by the user """
        quoted_args = [quote(str(arg)) for arg in args]
        results.append("aq %s --switch %s %s" % (cmd, dbswitch.primary_name,
                                                 " ".join(quoted_args)))

    def update_switch(dbmodel, serial_no, comments):
        """ Helper for updating core switch attributes, honouring dryrun """
        if dryrun:
            args = ["update_switch"]
            if dbmodel and dbmodel != dbswitch.model:
                args.extend(["--model", dbmodel.name,
                             "--vendor", dbmodel.vendor.name])
            if serial_no and serial_no != dbswitch.serial_no:
                args.extend(["--serial", serial_no])
            if comments and comments != dbswitch.comments:
                args.extend(["--comments", comments])
            aqcmd(*args)
        else:
            if dbmodel:
                dbswitch.model = dbmodel
            if serial_no:
                dbswitch.serial_no = serial_no
            if comments:
                dbswitch.comments = comments

    def del_address(iface, addr):
        """ Helper for deleting an IP address, honouring dryrun """
        if dryrun:
            aqcmd("del_interface_address", "--interface", iface.name,
                  "--ip", addr.ip)
        else:
            iface.assignments.remove(addr)
            session.flush()
            q = session.query(AddressAssignment.id)
            q = q.filter_by(network=addr.network, ip=addr.ip)
            if not q.first():
                q = session.query(ARecord)
                q = q.filter_by(network=addr.network, ip=addr.ip)
                map(delete_dns_record, q.all())

    def del_interface(iface):
        """ Helper for deleting an interface, honouring dryrun """
        if dryrun:
            aqcmd("del_interface", "--interface", iface.name)
        else:
            dbswitch.interfaces.remove(iface)

    def do_rename_interface(iface, new_name):
        """ Helper for renaming an interface, honouring dryrun """
        if dryrun:
            aqcmd("update_interface", "--interface", iface.name, "--rename_to",
                  new_name)
        else:
            rename_interface(session, iface, new_name)

    def add_interface(ifname, iftype):
        """ Helper for adding a new interface, honouring dryrun """
        if dryrun:
            aqcmd("add_interface", "--interface", ifname, "--type", iftype)
            # There's no Interface instace we could return here, but fortunately
            # nothing will use the returned value in dryrun mode
            return None
        else:
            return get_or_create_interface(session, dbswitch, name=ifname,
                                           interface_type=iftype)

    def add_address(iface, ifname, ip, label, relaxed):
        """ Helper for adding an IP address, honouring dryrun """
        if label:
            name = "%s-%s-%s" % (dbswitch.primary_name.fqdn.name, ifname,
                                 label)
        else:
            name = "%s-%s" % (dbswitch.primary_name.fqdn.name, ifname)
        fqdn = "%s.%s" % (name, dbswitch.primary_name.fqdn.dns_domain)

        if dryrun:
            args = ["add_interface_address", "--interface", ifname, "--ip", ip]
            if label:
                args.extend(["--label", label])
            aqcmd(*args)
        else:
            # Doing the DSDB update if the address existed before would be
            # tricky, so prevent that case by passing preclude=True
            dbdns_rec, newly_created = grab_address(session, fqdn, ip,
                                                    dbnet_env,
                                                    relaxed=relaxed,
                                                    preclude=True)
            assign_address(iface, ip, dbdns_rec.network, label=label)

    def add_router(ip):
        """ Helper command for managing router IPs, honouring dryrun """
        # TODO: the command should be configurable
        cmd = "qip-set-router %s" % ip
        if dryrun:
            results.append(cmd)
        else:
            # If we're not the authoritative source, then we can't just create
            # the RouterAddress directly. TODO: It should be configurable
            # whether we're authoritative for network data
            logger.client_info("You should run '%s'." % cmd)

    def warning(msg):
        """
        Helper for sending warning messages to the client

        We cannot use the side channel in dryrun mode, because the "aq
        show_switch" command does not issue show_request. So we need to embed
        the warnings in the output.
        """
        if dryrun:
            results.append("# Warning: " + msg)
        else:
            logger.client_info("Warning: " + msg)

    hostname = determine_helper_hostname(session, logger, config, dbswitch)
    if hostname:
        args = determine_helper_args(config)
        args.append(hostname)
    else:
        args = []

    args.extend([importer, str(dbswitch.primary_name)])

    try:
        out = run_command(args)
    except ProcessException, err:
        raise ArgumentError("Failed to run switch discovery: %s" % err)

    data = JSONDecoder().decode(out)

    # Safety net: if the discovery program did not manage to collect any usable
    # information, do not do anything.
    if not data["interfaces"]:
        raise ArgumentError("Discovery returned no interfaces, aborting.")

    if "model" in data and "vendor" in data:
        dbmodel = Model.get_unique(session, name=data["model"],
                                   vendor=data["vendor"])
    else:
        dbmodel = None

    if "serial" in data:
        serial_no = data["serial"]
    else:
        serial_no = None

    comments = dbswitch.comments or ""
    if "tags" in data:
        # Remove previous occurances of the tags to ensure consistent casing and
        # ordering
        for tag in data["tags"]:
            pat = re.compile(r"\b" + re.escape(tag) + r"\b", re.I)
            comments = pat.sub("", comments)

        comments = " ".join(data["tags"]) + " " + comments

        # Normalize white space
        comments = re.sub("\s+", " ", comments)
        comments = comments.strip()

    # This is the easy part, so deal with it first
    update_switch(dbmodel, serial_no, comments)

    primary_ip = dbswitch.primary_name.ip

    # Build a lookup table of discovered IP addresses
    ip_to_iface = {}
    networks = []
    for ifname, params in data["interfaces"].items():
        for ipstr, label in params["ip"].items():
            ip = IPv4Address(ipstr)
            try:
                dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
                ip_to_iface[ip] = {"name": ifname, "label": label}
                networks.append(dbnetwork)
            except NotFoundException:
                warning("Skipping IP address %s: network not found." % ip)

                # Avoid creating the interface if there are no valid IPs
                del params["ip"][ipstr]
                if not params["ip"]:
                    del data["interfaces"][ifname]

    # Some switches do not report their management IP address. In theory the
    # discovery script should fix that up, but better to be sure.
    if primary_ip not in ip_to_iface:
        for iface in dbswitch.interfaces:
            if primary_ip in iface.addresses:
                ip_to_iface[primary_ip] = {"name": iface.name, "label": ""}
        warning("Primary IP is not present in discovery data, keeping existing "
                "definition on interface %s." % ip_to_iface[primary_ip]["name"])

    if not dryrun:
        # Lock networks where we may want to register a new IP address
        networks.sort(key=attrgetter("id"))
        for dbnetwork in networks:
            dbnetwork.lock_row()

        # Lock the DNS domain, because we may want to add new entries
        dbswitch.primary_name.fqdn.dns_domain.lock_row()

    # Do a first pass over interfaces. We'll fill in a bunch of lookup tables to
    # help rename detection etc. later. The name_by_iface mapping is needed for
    # dryrun mode when we can't just update the name of the interface
    iface_by_name = {}
    name_by_iface = {}
    addr_by_ip = {}
    ifaces_to_delete = []
    for iface in dbswitch.interfaces[:]:
        delete_iface = False

        if iface in ifaces_to_delete:
            # We may get here if we figured out that an interface we enumerated
            # before should be renamed to the name of this interface
            continue

        if iface.name in data["interfaces"]:
            # No change to the interface, just do some administration
            iface_by_name[iface.name] = iface
            name_by_iface[iface] = iface.name
        else:
            # We don't have an interface with the same name. Check if a
            # discovered interface has our IP, and rename the existing interface
            # if that's the case.
            delete_iface = True
            if iface.assignments:
                ip = iface.assignments[0].ip
                if ip in ip_to_iface:
                    new_name = ip_to_iface[ip]["name"]
                    iface2 = first_of(dbswitch.interfaces,
                                      lambda i: i.name == new_name)
                    if iface2 and iface2.assignments:
                        # The target name already exists, it has other
                        # addresses, we have no choice than delete and re-add
                        # the addresses
                        pass
                    else:
                        # If the target name already exists but has no
                        # addresses, then we can delete it and rename the
                        # current interface
                        if iface2 and iface2 not in ifaces_to_delete:
                            ifaces_to_delete.append(iface2)
                        iface_by_name[new_name] = iface
                        name_by_iface[iface] = new_name
                        delete_iface = False

        # Make a copy of iface.assignments, because we want to modify it inside
        # the loop
        for addr in iface.assignments[:]:
            # We need to delete addresses that are gone. However we also need to
            # delete and re-add addresses if:
            # - the interface itself has to be deleted
            # - the interface is still there, but the IP address now belongs to
            #   a different interface
            # - the label have changed
            if delete_iface or addr.ip not in ip_to_iface or \
               ip_to_iface[addr.ip]["name"] != name_by_iface[iface] or \
               addr.label != ip_to_iface[addr.ip]["label"]:
                del_address(iface, addr)
            else:
                addr_by_ip[addr.ip] = addr

        if delete_iface:
            ifaces_to_delete.append(iface)

    for iface in ifaces_to_delete:
        del_interface(iface)
    del ifaces_to_delete[:]

    # Rename interfaces
    # TODO: cascaded renames (e1->e2, e2->e3) and loops (e1->e2, e2->e1) may not
    # be handled properly, and may need someone to break the cycles manually.
    # However such cases should be rare in real life, so probably it's not worth
    # spending too much effort dealing with them.
    for new_name, iface in iface_by_name.items():
        if iface.name == new_name:
            continue
        do_rename_interface(iface, new_name)

    # Add missing interfaces and addresses
    for ifname, params in data["interfaces"].items():
        if ifname in iface_by_name:
            iface = iface_by_name[ifname]
            # TODO: should we update the interface type here? There's no 'aq'
            # command to do that, and existing IP addresses may not be valid for
            # the new type (e.g. broadcast address on a non-loopback
            # interface)...
        else:
            iface = add_interface(ifname, params["type"])

        if params["type"] == "loopback":
            relaxed = True
        else:
            relaxed = False

        for ipstr, label in params["ip"].items():
            ip = IPv4Address(ipstr)

            if ip not in ip_to_iface:
                # Unknown network etc.
                continue

            if ip not in addr_by_ip:
                add_address(iface, ifname, ip, label, relaxed)

    # Check router addresses
    if "router_ips" in data:
        for ipstr in data["router_ips"]:
            ip = IPv4Address(ipstr)
            try:
                dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
                rtr = RouterAddress.get_unique(session, ip=ip,
                                               network=dbnetwork)
                if not rtr:
                    add_router(ip)
            except NotFoundException:
                warning("Skipping router IP address %s: network not found." %
                        ip)

    return results
