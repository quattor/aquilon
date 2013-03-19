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
""" Helper classes for chassis testing """


class VerifyChassisMixin(object):

    def verifychassis(self, chassis, vendor, model, rack, rackrow, rackcol,
                      serial=None, ip=None, mac=None, interface=None,
                      comments=None):
        command = "show chassis --chassis %s" % chassis
        out = self.commandtest(command.split(" "))
        (short, dot, dns_domain) = chassis.partition(".")
        self.matchoutput(out, "Chassis: %s" % short, command)
        if dns_domain:
            if ip:
                # Check both the primary name...
                self.matchoutput(out, "Primary Name: %s [%s]" %
                                 (chassis, ip), command)
                # ... and the AddressAssignment record
                self.matchoutput(out, "Provides: %s [%s]" %
                                 (chassis, ip), command)
            else:
                self.matchoutput(out, "Primary Name: %s" % chassis, command)
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

        if interface:
            self.matchclean(out, "\n    Comments: Created automatically",
                            command)
        else:
            # FIXME: eventually this should be part of the model
            interface = "oa"
            self.matchoutput(out, "\n    Comments: Created automatically "
                             "by add_chassis", command)
        if mac:
            self.searchoutput(out, r"Interface: %s %s$" % (interface, mac),
                              command)
        else:
            self.searchoutput(out, r"Interface: %s \(no MAC addr\)$" %
                              interface, command)

        return (out, command)
