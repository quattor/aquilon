# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2018  Contributor
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
""" Helper classes for chassis testing """


class VerifyConsoleServerMixin(object):

    def verifyconsoleserver(self, console_server, vendor, model, rack, rackrow, rackcol,
                      serial=None, ip=None, mac=None, interface='mgmt',
                      comments=None, ports=None):
        command = "show console_server --console_server %s" % console_server
        out = self.commandtest(command.split(" "))
        (short, _, dns_domain) = console_server.partition(".")
        self.matchoutput(out, "Console Server: %s" % short, command)
        if dns_domain:
            if ip:
                # Check both the primary name...
                self.matchoutput(out, "Primary Name: %s [%s]" %
                                 (console_server, ip), command)
                # ... and the AddressAssignment record
                self.matchoutput(out, "Provides: %s [%s]" %
                                 (console_server, ip), command)
            else:
                self.matchoutput(out, "Primary Name: %s" % console_server, command)
        self.matchoutput(out, "Rack: %s" % rack, command)
        self.matchoutput(out, "Row: %s" % rackrow, command)
        self.matchoutput(out, "Column: %s" % rackcol, command)
        self.matchoutput(out, "Vendor: %s Model: %s" % (vendor, model),
                         command)
        if serial:
            self.matchoutput(out, "Serial: %s" % serial, command)
        else:
            self.matchclean(out, "Serial:", command)

        # Careful about indentation, do not mix chassis comments with interface
        # comments
        if comments:
            self.matchoutput(out, "\n  Comments: %s" % comments, command)
        else:
            self.matchclean(out, "\n  Comments:", command)

        if mac:
            self.searchoutput(out, r"Interface: %s %s$" % (interface, mac),
                              command)
        else:
            self.searchoutput(out, r"Interface: %s \(no MAC addr\)$" %
                              interface, command)
        if ports:
            for port in ports:
                self.searchoutput(out, "Port %s: %s %s" % (port[0], port[1], port[2]), command)

        return (out, command)
