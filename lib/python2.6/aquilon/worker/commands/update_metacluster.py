# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import MetaCluster
from aquilon.exceptions_ import ArgumentError


class CommandUpdateMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    def render(self, session, metacluster, max_members, max_shares,
               high_availability, comments, **arguments):
        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)
        if max_members is not None:
            current_members = len(dbmetacluster.members)
            if max_members < current_members:
                raise ArgumentError("%s has %d clusters bound, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbmetacluster), current_members,
                                     max_members))
            dbmetacluster.max_clusters = max_members

        if max_shares is not None:
            current_shares = len(dbmetacluster.shares)
            if max_shares < current_shares:
                raise ArgumentError("%s has %d shares attached, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbmetacluster), current_shares,
                                     max_shares))
            dbmetacluster.max_shares = max_shares

        if comments is not None:
            dbmetacluster.comments = comments

        if high_availability is not None:
            dbmetacluster.high_availability = high_availability

        session.add(dbmetacluster)
        session.flush()
        dbmetacluster.validate()

        return
