# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016,2017  Contributor
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
""" Helper classes for machine testing """

from collections import defaultdict
import json
from eventstest import EventsTestMixin


class MachineData(object):
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.comments = None
        self.interfaces = {}
        self.disks = {}
        self.manager_iface = None
        self.manager_ip = None
        # Other attributes are created on-demand based on the parameters. If you
        # need some attribute (e.g. memory) always avilable, initialize it to
        # None here.


def guess_interfaces(kwargs, eth0_default=True):
    ifnames = set()

    if eth0_default:
        ifnames.add("eth0")

    for arg in kwargs:
        if arg.endswith("_ip") or arg.endswith("_pg"):
            ifnames.add(arg[0:-3])
        elif arg.endswith("_mac"):
            ifnames.add(arg[0:-4])

    return sorted(ifnames)


def guess_disks(kwargs):
    disks = set()

    disks.update(arg[0:-5] for arg in kwargs if arg.endswith("_size"))
    return sorted(disks)


class MachineTestMixin(EventsTestMixin):
    def verify_show_machine(self, name, interfaces=None, zebra=False, model=None,
                            vendor=None, cluster=None, vmhost=None, memory=None,
                            **kwargs):
        if not interfaces:
            interfaces = guess_interfaces(kwargs)
        disks = guess_disks(kwargs)

        # Now do some basic tests. We cannot test for information that was not
        # specified directly but comes from other sources (defaults, model
        # definition etc.), that should be done in the caller when needed.
        show_cmd = ["show_machine", "--machine", name]
        show_out = self.commandtest(show_cmd)

        if cluster:
            self.matchoutput(show_out, "Hosted by: ESX Cluster %s" % cluster,
                             show_cmd)
        if vmhost:
            self.matchoutput(show_out, "Hosted by: Host %s" % vmhost, show_cmd)

        for arg in ["desk", "chassis", "slot", "serial"]:
            if arg in kwargs:
                self.matchoutput(show_out, "%s: %s" %
                                 (arg.title(), kwargs[arg]), show_cmd)
            else:
                self.matchclean(show_out, arg.title(), show_cmd)

        # No matchclean() for comments - interfaces, disks, etc. may also have
        # comments
        if "comments" in kwargs:
            self.matchoutput(show_out, "Comments: %s" % kwargs["comments"],
                             show_cmd)

        # Specifying chassis will put the machine inside a rack, so we can't use
        # matchclean() if the rack was not specified explicitly
        if "rack" in kwargs:
            self.matchoutput(show_out, "Rack: %s" % kwargs["rack"], show_cmd)

        if memory:
            self.matchoutput(show_out, "Memory: %d MB" % memory, show_cmd)
        if model and vendor:
            self.matchoutput(show_out, "Vendor: %s Model: %s" % (vendor, model),
                             show_cmd)

        if "cpuname" and "cpucount" in kwargs:
            self.matchoutput(show_out, "Cpu: %s x %d" %
                             (kwargs["cpuname"], kwargs["cpucount"]),
                             show_cmd)

        iface_params = defaultdict(dict)
        for nic_name in interfaces:
            for name, value in kwargs.items():
                if name.startswith(nic_name + "_"):
                    iface_params[nic_name][name[len(nic_name) + 1:]] = value

        for nic_name, params in iface_params.items():
            if nic_name == "eth0":
                flagstr = r" \[boot, default_route\]"
            elif zebra and nic_name == "eth1":
                flagstr = r" \[default_route\]"
            else:
                flagstr = ""

            if "mac" in params:
                regexp = r"Interface: %s %s%s$" % (nic_name, params["mac"],
                                                   flagstr)
            else:
                regexp = r"Interface: %s \(no MAC addr\)%s$" % (nic_name,
                                                                flagstr)

            # This line may be present if the interface was added after the
            # switch was polled
            regexp += r"(\s+Last switch poll:.*$)?"

            regexp += r"\s+Type: public$"
            if "model" in params:
                if "vendor" in params:
                    vendor = params["vendor"]
                else:
                    vendor = ".*"
                regexp += r"\s+Vendor: %s Model: %s$" % (vendor, params["model"])
            else:
                regexp += r"\s+Vendor: generic Model: generic_nic$"

            if "pg" in params:
                regexp += r"\s+Port Group: %s" % params["pg"]
                # TODO: We don't know the network, and there's no network when
                # --pg is used for physical machines
                regexp += r"(\s+Network: .*\[.*/.*\])?"

            if "ip" in params:
                regexp += r"\s+Network Environment: internal$"
                regexp += r"\s+Provides: %s \[%s\]$" % (
                    params["fqdn"].replace(".", r"\."),
                    str(params["ip"]).replace(".", r"\."))
            else:
                # FIXME: If the IP was passed to create_host(), then it will not
                # be part of the per-interface parameters
                regexp += r"(\s+Network Environment:.*$\s+Provides:.*$)?"

            if "comments" in params:
                regexp += r"\s+Comments: %s$" % params["comments"]

            self.searchoutput(show_out, regexp, show_cmd)

        disk_params = defaultdict(dict)
        for disk_name in disks:
            for name, value in kwargs.items():
                if name.startswith(disk_name + "_"):
                    disk_params[disk_name][name[len(disk_name) + 1:]] = value

        for disk_name, params in disk_params.items():
            regexp = r"Disk: %s %d GB %s \(local\).*$\s*" % (
                disk_name, params["size"], params["controller"])
            if "address" in params:
                regexp += "Address: " + params["address"] + r"\s*"
            if "wwn" in params:
                regexp += "WWN: " + params["wwn"] + r"\s*"
            if "bus_address" in params:
                regexp += "Controller Bus Address: " + params["bus_address"] + r"\s*"

            self.searchoutput(show_out, regexp, show_cmd)

        # Allow the caller to do further testing if it wants
        return (show_cmd, show_out)

    def create_machine(self, name, model, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = guess_interfaces(kwargs)

        machdef = MachineData(name, model)
        recipe = {}

        # We assume the vendor will be guessed
        add_machine_args = ["--machine", name, "--model", model]

        # Options which must be passed on the command line
        for optional in ["chassis", "slot", "serial", "comments",
                         "cluster", "vmhost", "rack", "desk"]:
            if optional not in kwargs:
                continue
            value = kwargs.pop(optional)
            if value is None:
                continue
            setattr(machdef, optional, value)
            add_machine_args.extend(["--" + optional, value])

        # Options which can be passed as recipe
        for optional in ["cpucount", "cpuvendor", "cpuname", "memory"]:
            if optional not in kwargs:
                continue
            value = kwargs.pop(optional)
            if value is None:
                continue
            setattr(machdef, optional, value)
            recipe[optional] = value

        if interfaces:
            recipe["interfaces"] = defaultdict(dict)

        for nic_name in interfaces:
            params = {}

            for arg_name in ["mac", "pg", "model", "vendor", "comments"]:
                if nic_name + "_" + arg_name in kwargs:
                    value = kwargs.pop(nic_name + "_" + arg_name)
                    if value is None:
                        continue
                    params[arg_name] = value
                    recipe["interfaces"][nic_name][arg_name] = value

            # Skip parameters not relevant for add_machine (e.g. IP address)
            for arg_name in kwargs.keys()[:]:
                if arg_name.startswith(nic_name + "_"):
                    value = kwargs.pop(arg_name)
                    if value is None:
                        continue
                    params[arg_name[len(nic_name) + 1:]] = value

            machdef.interfaces[nic_name] = params

        disks = guess_disks(kwargs)
        if disks:
            recipe["disks"] = {}

        for disk_name in disks:
            params = {}
            for arg_name in ["size", "controller", "address", "wwn",
                             "bus_address", "share",
                             "filesystem", "resourcegroup"]:
                if disk_name + "_" + arg_name in kwargs:
                    value = kwargs.pop(disk_name + "_" + arg_name)
                    if value is None:
                        continue
                    params[arg_name] = value

            machdef.disks[disk_name] = params
            recipe["disks"][disk_name] = params

        if recipe:
            add_machine_args.append("--recipe")
            add_machine_args.append(json.dumps(recipe))

        self.noouttest(["add_machine"] + add_machine_args)

        if kwargs:
            raise ValueError("Unprocessed arguments: %r" % kwargs)

        return machdef

    def create_machine_hs21(self, name, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = guess_interfaces(kwargs)

        self.create_machine(name, "hs21-8853", interfaces, **kwargs)

        # Now fill in default values needed for verification
        kwargs["model"] = "hs21-8853"
        if "vendor" not in kwargs:
            kwargs["vendor"] = "ibm"
        if "cpuname" not in kwargs:
            kwargs["cpuname"] = "e5-2660"
        if "cpucount" not in kwargs:
            kwargs["cpucount"] = 2
        if "memory" not in kwargs:
            kwargs["memory"] = 8192

        show_cmd, show_out = self.verify_show_machine(name, interfaces,
                                                      **kwargs)
        self.matchoutput(show_out, "Machine: %s" % name.lower(), show_cmd)
        self.matchoutput(show_out, "Model Type: blade", show_cmd)
        self.matchclean(show_out, "Primary Name:", show_cmd)
        return show_cmd, show_out

    def create_machine_dl360g9(self, name, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = guess_interfaces(kwargs)

        self.create_machine(name, "dl360g9", interfaces, **kwargs)

        # Now fill in default values needed for verification
        kwargs["model"] = "dl360g9"
        if "vendor" not in kwargs:
            kwargs["vendor"] = "hp"
        if "cpuname" not in kwargs:
            kwargs["cpuname"] = "e5-2660-v3"
        if "cpucount" not in kwargs:
            kwargs["cpucount"] = 2
        if "memory" not in kwargs:
            # TODO: update this to something more realistic...
            kwargs["memory"] = 24576

        show_cmd, show_out = self.verify_show_machine(name, interfaces,
                                                      **kwargs)
        self.matchoutput(show_out, "Machine: %s" % name.lower(), show_cmd)
        self.matchoutput(show_out, "Model Type: rackmount", show_cmd)
        self.matchclean(show_out, "Primary Name:", show_cmd)
        return show_cmd, show_out

    def create_host(self, hostname, ip, machine,
                    interfaces=None, zebra=False, model=None,
                    manager_iface=None, manager_ip=None,
                    archetype="aquilon", ipfromtype=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()

        # Separate the host-specific arguments
        host_kwargs = {}
        for arg in ["domain", "sandbox", "personality", "personality_stage",
                    "osname", "osversion", "buildstatus", "grn", "eon_id"]:
            if arg in kwargs:
                host_kwargs[arg] = kwargs.pop(arg)

        short_hostname, dns_domain = hostname.split(".", 1)

        if not interfaces:
            interfaces = guess_interfaces(kwargs)
            if "eth0_mac" not in kwargs:
                kwargs["eth0_mac"] = ip.mac

        if "domain" not in host_kwargs and "sandbox" not in host_kwargs:
            host_kwargs["domain"] = "unittest"

        machdef = self.create_machine(machine, model, interfaces, **kwargs)

        command = ["add_host", "--hostname", hostname,
                   "--machine", machine, "--archetype", archetype]
        for arg, value in host_kwargs.items():
            if value is None:
                continue
            command.extend(["--" + arg, value])

        if zebra:
            self.dsdb_expect_add(hostname, ip, "vip", comments=machdef.comments)
            if ipfromtype is not None:
                command.extend(["--zebra_interfaces", ",".join(interfaces), "--ipfromtype", ipfromtype])
            else:
                command.extend(["--zebra_interfaces", ",".join(interfaces), "--ip", ip])
        else:
            # FIXME: do not hardcode eth0?
            if "eth0_comments" in orig_kwargs:
                comments = orig_kwargs["eth0_comments"]
            else:
                comments = machdef.comments
            self.dsdb_expect_add(hostname, ip, "eth0", ip.mac, comments=comments)
            command.extend(["--ip", ip])

        self.noouttest(command)

        for nic_name, params in machdef.interfaces.items():
            if "ip" not in params:
                continue

            if "fqdn" in params:
                fqdn = params["fqdn"]
            else:
                fqdn = "%s-%s.%s" % (short_hostname, nic_name, dns_domain)
                params["fqdn"] = fqdn
                kwargs[nic_name + "_fqdn"] = fqdn

            self.dsdb_expect_add(fqdn, params["ip"], nic_name, params["mac"],
                                 primary=hostname)
            self.statustest(["add_interface_address", "--machine", machine,
                             "--interface", nic_name, "--ip", params["ip"],
                             "--fqdn", fqdn])

        self.dsdb_verify()

        if manager_iface:
            command = ["add_manager", "--hostname", hostname,
                       "--interface", manager_iface,
                       "--ip", manager_ip, "--mac", manager_ip.mac]
            short, domain = hostname.split(".", 1)
            self.dsdb_expect_add(short + "r." + domain, manager_ip,
                                 manager_iface, manager_ip.mac)
            self.noouttest(command)
            self.dsdb_verify()

        show_cmd, show_out = self.verify_show_machine(machine, interfaces,
                                                      zebra=zebra, **kwargs)
        self.matchoutput(show_out, "Primary Name: %s [%s]" % (hostname, ip),
                         show_cmd)
        for nic_name, params in machdef.interfaces.items():
            if "ip" not in params:
                continue
            self.matchoutput(show_out, "Auxiliary: %s [%s]" % (params["fqdn"],
                                                               params["ip"]),
                             show_cmd)
        if manager_iface:
            short, domain = hostname.split(".", 1)
            self.matchoutput(show_out, "Manager: %sr.%s [%s]" %
                             (short, domain, manager_ip), command)
        return show_cmd, show_out

    def delete_host(self, hostname, ip, machine, interfaces=None,
                    manager_ip=None, justification=None, **kwargs):
        if not interfaces:
            interfaces = guess_interfaces(kwargs, eth0_default=False)

        for nic_name in interfaces:
            nic_ip = kwargs.get(nic_name + "_ip", None)
            if nic_ip and nic_ip != ip:
                self.dsdb_expect_delete(nic_ip)
                if justification:
                    command = ["del_interface_address", "--machine", machine,
                               "--interface", nic_name, "--ip", nic_ip] + self.valid_just_tcm
                    self.statustest(command)
                else:
                    self.statustest(["del_interface_address", "--machine", machine,
                                     "--interface", nic_name, "--ip", nic_ip])
                self.dsdb_verify()

        self.dsdb_expect_delete(ip)
        if justification:
            command = ["del_host", "--hostname", hostname] + self.valid_just_tcm
            self.statustest(command)
        else:
            self.statustest(["del_host", "--hostname", hostname])
        if manager_ip:
            self.dsdb_expect_delete(manager_ip)
            short, domain = hostname.split(".", 1)
            if justification:
                command = ["del_manager", "--manager", "%sr.%s" %
                          (short, domain)] + self.valid_just_tcm
                self.noouttest(command)
            else:
                self.noouttest(["del_manager", "--manager", "%sr.%s" %
                            (short, domain)])
        self.noouttest(["del_machine", "--machine", machine])
        self.dsdb_verify()
