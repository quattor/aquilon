# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Helper classes for network device testing """


class VerifyNetworkDeviceMixin(object):

    def verifynetdev(self, netdev, vendor, model,
                     rack, rackrow, rackcol,
                     serial=None, switch_type='tor', ip=None, mac=None,
                     interface=None, comments=None):
        command = "show network device --network_device %s" % netdev
        out = self.commandtest(command.split(" "))
        (short, dot, dns_domain) = netdev.partition(".")
        self.matchoutput(out, "Switch: %s" % short, command)
        if dns_domain:
            if ip:
                # Check both the primary name...
                self.matchoutput(out, "Primary Name: %s [%s]" % (netdev, ip),
                                 command)
                # ... and the AddressAssignment record
                self.matchoutput(out, "Provides: %s [%s]" % (netdev, ip),
                                 command)
            else:
                self.matchoutput(out, "Primary Name: %s" % netdev, command)
        self.matchoutput(out, "Switch Type: %s" % switch_type, command)
        self.matchoutput(out, "Rack: %s" % rack, command)
        self.matchoutput(out, "Row: %s" % rackrow, command)
        self.matchoutput(out, "Column: %s" % rackcol, command)
        self.matchoutput(out, "Vendor: %s Model: %s" % (vendor, model),
                         command)
        if serial:
            self.matchoutput(out, "Serial: %s" % serial, command)
        else:
            self.matchclean(out, "Serial:", command)

        # Careful about indentation, do not mistake switch comments with
        # interface comments
        if comments:
            self.matchoutput(out, "\n  Comments: %s" % comments, command)
        else:
            self.matchclean(out, "\n  Comments:", command)

        if interface:
            self.matchclean(out, "\n    Comments: Created automatically",
                            command)
        else:
            # FIXME: eventually this should be part of the model
            interface = "xge"
            self.searchoutput(out, "^    Comments: Created automatically",
                              command)
        if mac:
            self.searchoutput(out, r"Interface: %s %s$" % (interface, mac),
                              command)
        else:
            self.searchoutput(out, r"Interface: %s \(no MAC addr\)$" %
                              interface, command)
#        for port in range(1,49):
#            self.matchoutput(out, "Switch Port %d" % port, command)
        return (out, command)
