# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011  Contributor
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


from aquilon.aqdb.model import Filesystem
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddFilesystem(BrokerCommand):

    required_parameters = ["filesystem", "mountpoint", "blockdevice",
                           "type", "bootmount"]

    def render(self, session, logger, filesystem, type, mountpoint,
               blockdevice, bootmount,
               dumpfreq, fsckpass, options,
               hostname, cluster, resourcegroup,
               comments, **arguments):

        validate_basic("filesystem", filesystem)
        holder = get_resource_holder(session, hostname, cluster, resourcegroup,
                                     compel=False)

        Filesystem.get_unique(session, name=filesystem, holder=holder,
                              preclude=True)

        if dumpfreq is None:
            dumpfreq = 0
        if fsckpass is None:
            # This is already set by defaults in input.xml, but
            # we're being extra paranoid...
            fsckpass = 2  # pragma: no cover

        dbfs = Filesystem(name=filesystem,
                          mountpoint=mountpoint,
                          mountoptions=options,
                          mount=bool(bootmount),
                          blockdev=blockdevice,
                          fstype=type,
                          passno=fsckpass,
                          dumpfreq=dumpfreq,
                          comments=comments
                          )

        return add_resource(session, logger, holder, dbfs)
