# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""System formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import System


# Should never get invoked...
class SystemFormatter(ObjectFormatter):
    def format_raw(self, system, indent=""):
        details = [indent + "%s: %s" % (system.system_type, system.fqdn)]
        if system.ip:
            details.append(indent + "  IP: %s" % system.ip)
        if system.mac:
            details.append(indent + "  MAC: %s" % system.mac)
        if system.comments:
            details.append(indent + "  Comments: %s" % system.comments)
        return "\n".join(details)

ObjectFormatter.handlers[System] = SystemFormatter()


class SimpleSystemList(list):
    """By convention, holds a list of systems to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleSystemListFormatter(ListFormatter):
    def format_raw(self, sslist, indent=""):
        return str("\n".join([indent + system.fqdn for system in sslist]))

    # TODO: Should probably display some useful info...
    def csv_fields(self, system):
        return (system.fqdn,)

    def format_html(self, sslist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/system/%(fqdn)s.html">%(fqdn)s</a></li>"""
            % {"fqdn": system.fqdn} for system in sslist])

ObjectFormatter.handlers[SimpleSystemList] = SimpleSystemListFormatter()
