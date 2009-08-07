# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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


from aquilon.server.broker import BrokerCommand, validate_basic, force_int
from aquilon.aqdb.model import MetaCluster
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.location import get_location


class CommandUpdateMetaCluster(BrokerCommand):

    required_parameters = [ "metacluster" ]

    def render(self, session, metacluster, max_members, max_shares, comments,
               **arguments):
        q = session.query(MetaCluster).filter_by(name=metacluster)
        dbmetacluster = q.first()
        if not dbmetacluster:
            raise NotFoundException("metacluster '%s' not found" % metacluster)

        max_members = force_int("max_members", max_members)
        if max_members is not None:
            if len(dbmetacluster.members) > max_members:
                raise ArgumentError("metacluster %s already exceeds %s "
                                    "max_members with %s clusters currently "
                                    "bound" %
                                    (dbmetacluster.name, max_members,
                                     len(dbmetacluster.members)))
            dbmetacluster.max_clusters = max_members

        max_shares = force_int("max_shares", max_shares)
        if max_shares is not None:
            current_shares = len(dbmetacluster.shares)
            if max_shares < current_shares:
                raise ArgumentError("Cannot set max_shares to %s: Metacluster "
                                    "%s has %s shares already attached." %
                                    (max_shares, dbmetacluster.name,
                                     current_shares))
            dbmetacluster.max_shares = max_shares

        if comments is not None:
            dbmetacluster.comments = comments

        session.add(dbmetacluster)

        return


