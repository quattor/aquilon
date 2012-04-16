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
"""VirtualMachine Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import VirtualMachine


class VirtualMachineFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, vm, indent=""):
        # There will be a lot of VMs attached to a cluster, so be terse.
        dbmachine = vm.machine
        if dbmachine.primary_name:
            name = dbmachine.primary_name.fqdn
        else:
            name = "no hostname"

        # TODO: report GB instead of MB?
        return indent + "%s: %s (%s, %d MB)" % (
            vm._get_class_label(), dbmachine.label, name, dbmachine.memory)

    def format_proto(self, vm, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        return super(VirtualMachineFormatter, self).format_proto(vm, skeleton)


ObjectFormatter.handlers[VirtualMachine] = VirtualMachineFormatter()
