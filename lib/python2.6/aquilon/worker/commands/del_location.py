# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq del location`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (Location, Network, NetworkEnvironment, Cluster,
                                HardwareEntity)


class CommandDelLocation(BrokerCommand):

    required_parameters = ["name", "type"]

    def render(self, session, name, type, **arguments):
        dblocation = Location.get_unique(session, name=name, location_type=type,
                                         compel=True)

        q = session.query(Network).filter_by(location=dblocation)
        if q.count():
            raise ArgumentError("Could not delete {0:l}, networks were found "
                                "using this location.".format(dblocation))

        q = session.query(NetworkEnvironment).filter_by(location=dblocation)
        if q.count():
            raise ArgumentError("Could not delete {0:l}, network environments "
                                "were found using this location."
                                .format(dblocation))

        q = session.query(Cluster).filter_by(location_constraint=dblocation)
        if q.count():
            raise ArgumentError("Could not delete {0:l}, clusters were found "
                                "using this location.".format(dblocation))

        q = session.query(HardwareEntity).filter_by(location=dblocation)
        if q.count():
            raise ArgumentError("Could not delete {0:l}, hardware objects were "
                                "found using this location.".format(dblocation))

        session.delete(dblocation)
        return
