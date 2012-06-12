# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
""" Helper classes for switch testing """


class VerifySwitchMixin(object):

    def verifyswitch(self, switch, vendor, model,
                     rack, rackrow, rackcol,
                     serial=None, switch_type='tor', ip=None, mac=None,
                     interface=None, comments=None):
        command = "show switch --switch %s" % switch
        out = self.commandtest(command.split(" "))
        (short, dot, dns_domain) = switch.partition(".")
        self.matchoutput(out, "Switch: %s" % short, command)
        if dns_domain:
            if ip:
                # Check both the primary name...
                self.matchoutput(out, "Primary Name: %s [%s]" % (switch, ip),
                                 command)
                # ... and the AddressAssignment record
                self.matchoutput(out, "Provides: %s [%s]" % (switch, ip),
                                 command)
            else:
                self.matchoutput(out, "Primary Name: %s" % switch, command)
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
            self.searchoutput(out, "^    Comments: Created automatically "
                             "by add_(tor_)?switch", command)
        if mac:
            self.searchoutput(out, r"Interface: %s %s$" % (interface, mac),
                              command)
        else:
            self.searchoutput(out, r"Interface: %s \(no MAC addr\)$" %
                              interface, command)
#        for port in range(1,49):
#            self.matchoutput(out, "Switch Port %d" % port, command)
        return (out, command)

