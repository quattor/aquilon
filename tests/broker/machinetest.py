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


class MachineTestMixin(object):
    def verify_show_machine(self, name, interfaces=None, model=None,
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
            else:
                flagstr = r""

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

            self.searchoutput(show_out, regexp, show_cmd)

        # Allow the caller to do further testing if it wants
        return (show_cmd, show_out)

    def create_machine(self, name, model, interfaces=None, **orig_kwargs):
        kwargs = orig_kwargs.copy()
        if not interfaces:
            interfaces = ["eth0"]

        # We assume the vendor will be guessed
        add_machine_args = ["--machine", name,
                            "--model", model]

        for optional in ["cpucount", "cpuvendor", "cpuname", "cpuspeed",
                         "memory", "chassis", "slot", "serial", "comments",
                         "cluster", "vmhost", "rack", "desk"]:
            if optional not in kwargs:
                continue
            value = kwargs.pop(optional)
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

        if kwargs:
            raise ValueError("Unprocessed arguments: %r" % kwargs)

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
        self.matchoutput(show_out, "Blade: %s" % name.lower(), show_cmd)
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
        self.matchoutput(show_out, "Blade: %s" % name.lower(), show_cmd)
        self.matchclean(show_out, "Primary Name:", show_cmd)
        return show_cmd, show_out
