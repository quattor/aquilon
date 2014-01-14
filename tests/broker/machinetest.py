# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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


class MachineData(object):
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.comments = None
        self.interfaces = {}
        # Other attributes are created on-demand based on the parameters. If you
        # need some attribute (e.g. memory) always avilable, initialize it to
        # None here.


class MachineTestMixin(object):
    def verify_show_machine(self, name, interfaces=None, zebra=False, model=None,
                            vendor=None, cluster=None, vmhost=None, memory=None,
                            **kwargs):
        if not interfaces:
            interfaces = ["eth0"]

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

        for arg in ["rack", "desk", "chassis", "slot", "serial", "comments"]:
            if arg in kwargs:
                self.matchoutput(show_out, "%s: %s" %
                                 (arg.title(), kwargs[arg]), show_cmd)
            else:
                self.matchclean(show_out, arg.title(), show_cmd)

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

            if "ip" in params:
                regexp += r"\s+Network Environment: internal$"
                regexp += r"\s+Provides: %s \[%s\]$" % (
                    params["fqdn"].replace(".", r"\."),
                    str(params["ip"]).replace(".", r"\."))

            self.searchoutput(show_out, regexp, show_cmd)

        # Allow the caller to do further testing if it wants
        return (show_cmd, show_out)

    def create_machine(self, name, model, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = ["eth0"]

        machdef = MachineData(name, model)

        # We assume the vendor will be guessed
        add_machine_args = ["--machine", name,
                            "--model", model]

        for optional in ["cpucount", "cpuvendor", "cpuname", "cpuspeed",
                         "memory", "chassis", "slot", "serial", "comments",
                         "cluster", "vmhost", "rack", "desk"]:
            if optional not in kwargs:
                continue
            value = kwargs.pop(optional)
            setattr(machdef, optional, value)
            add_machine_args.extend(["--" + optional, value])

        self.noouttest(["add_machine"] + add_machine_args)

        for nic_name in interfaces:
            params = {}
            add_iface_args = ["add_interface", "--machine", name,
                              "--interface", nic_name]
            add_ifaddr_args = ["add_interface_address", "--machine", name,
                               "--interface", nic_name]

            for arg_name in ["mac", "pg", "model", "vendor"]:
                if nic_name + "_" + arg_name in kwargs:
                    value = kwargs.pop(nic_name + "_" + arg_name)
                    add_iface_args.extend(["--" + arg_name, value])
                    params[arg_name] = value

            needs_addr = False
            for arg_name in ["ip", "fqdn"]:
                if nic_name + "_" + arg_name in kwargs:
                    value = kwargs.pop(nic_name + "_" + arg_name)
                    add_ifaddr_args.extend(["--" + arg_name, value])
                    params[arg_name] = value
                    needs_addr = True

            self.noouttest(add_iface_args)
            if needs_addr:
                self.dsdb_expect_add(params["fqdn"], params["ip"], nic_name,
                                     params["mac"])
                self.noouttest(add_ifaddr_args)
                self.dsdb_verify()

            machdef.interfaces[nic_name] = params

        if kwargs:
            raise ValueError("Unprocessed arguments: %r" % kwargs)

        return machdef

    def create_machine_hs21(self, name, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = ["eth0"]

        self.create_machine(name, "hs21-8853l5u", interfaces, **kwargs)

        # Now fill in default values needed for verification
        kwargs["model"] = "hs21-8853l5u"
        if "vendor" not in kwargs:
            kwargs["vendor"] = "ibm"
        if "cpuname" not in kwargs:
            kwargs["cpuname"] = "xeon_2660"
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

    def create_machine_verari(self, name, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = ["eth0"]

        self.create_machine(name, "vb1205xm", interfaces, **kwargs)

        # Now fill in default values needed for verification
        kwargs["model"] = "vb1205xm"
        if "vendor" not in kwargs:
            kwargs["vendor"] = "verari"
        if "cpuname" not in kwargs:
            kwargs["cpuname"] = "xeon_2500"
        if "cpucount" not in kwargs:
            kwargs["cpucount"] = 2
        if "memory" not in kwargs:
            kwargs["memory"] = 24576

        show_cmd, show_out = self.verify_show_machine(name, interfaces,
                                                      **kwargs)
        self.matchoutput(show_out, "Machine: %s" % name.lower(), show_cmd)
        self.matchoutput(show_out, "Model Type: blade", show_cmd)
        self.matchclean(show_out, "Primary Name:", show_cmd)
        return show_cmd, show_out

    def create_host(self, hostname, ip, machine,
                    interfaces=None, zebra=False, model=None,
                    archetype="aquilon", **orig_kwargs):
        kwargs = orig_kwargs.copy()

        # Separate the host-specific arguments
        host_kwargs = {}
        for arg in ["domain", "sandbox", "personality", "osname", "osversion",
                    "buildstatus", "grn", "eon_id"]:
            if arg in kwargs:
                host_kwargs[arg] = kwargs.pop(arg)

        if not interfaces:
            interfaces = ["eth0"]
            if "eth0_mac" not in kwargs:
                kwargs["eth0_mac"] = ip.mac

        if "domain" not in host_kwargs and "sandbox" not in host_kwargs:
            host_kwargs["domain"] = "unittest"

        machdef = self.create_machine(machine, model, interfaces, **kwargs)

        for nic_name, params in machdef.interfaces.items():
            if "ip" not in params:
                continue
            self.dsdb_expect_delete(params["ip"])
            self.dsdb_expect_add(params["fqdn"], params["ip"], nic_name,
                                 params["mac"], primary=hostname)

        command = ["add_host", "--hostname", hostname, "--ip", ip,
                   "--machine", machine, "--archetype", archetype]
        for arg, value in host_kwargs.items():
            command.extend(["--" + arg, value])

        if zebra:
            self.dsdb_expect_add(hostname, ip, "le0", comments=machdef.comments)
            command.extend(["--zebra_interfaces", ",".join(interfaces)])
        else:
            # FIXME: do not hardcode eth0?
            self.dsdb_expect_add(hostname, ip, "eth0", ip.mac, comments=machdef.comments)

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
        return show_cmd, show_out

    def delete_host(self, hostname, ip, machine, interfaces=None, **kwargs):
        if not interfaces:
            interfaces = []

        for nic_name in interfaces:
            nic_ip = kwargs.get(nic_name + "_ip", None)
            if nic_ip and nic_ip != ip:
                self.dsdb_expect_delete(nic_ip)
                self.noouttest(["del_interface_address", "--machine", machine,
                               "--interface", nic_name, "--ip", nic_ip])
                self.dsdb_verify()

        self.dsdb_expect_delete(ip)
        self.statustest(["del_host", "--hostname", hostname])
        self.dsdb_verify()

        self.noouttest(["del_machine", "--machine", machine])
