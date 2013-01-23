# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Filesystem Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Filesystem


class FilesystemFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, fs, indent=""):
        details = []
        details.append(indent + "  Block Device: %s" % fs.blockdev)
        details.append(indent + "  FSType: %s" % fs.fstype)
        details.append(indent + "  Mount at boot: %s" % fs.mount)
        details.append(indent + "  Mountopts: %s" % fs.mountoptions)
        details.append(indent + "  Mountpoint: %s" % fs.mountpoint)
        details.append(indent + "  Dump Freq: %d" % fs.dumpfreq)
        details.append(indent + "  Fsck Pass: %d" % fs.passno)
        return details

    def format_proto(self, fs, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        skeleton.fsdata.mount = fs.mount
        skeleton.fsdata.fstype = str(fs.fstype)
        skeleton.fsdata.blockdevice = str(fs.blockdev)
        skeleton.fsdata.mountpoint = str(fs.mountpoint)
        skeleton.fsdata.opts = str(fs.mountoptions)
        skeleton.fsdata.freq = fs.dumpfreq
        skeleton.fsdata.passno = fs.passno
        return super(FilesystemFormatter, self).format_proto(fs, skeleton)


ObjectFormatter.handlers[Filesystem] = FilesystemFormatter()
