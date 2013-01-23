# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
from aquilon.worker.commands.update_cluster import update_cluster_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue, CompileKey


class CommandUpdateMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    def render(self, session, logger, metacluster, max_members, max_shares,
               fix_location, high_availability, comments, **arguments):
        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)
        cluster_updated = False

        if max_members is not None:
            current_members = len(dbmetacluster.members)
            if max_members < current_members:
                raise ArgumentError("%s has %d clusters bound, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbmetacluster), current_members,
                                     max_members))
            dbmetacluster.max_clusters = max_members
            cluster_updated = True

        if max_shares is not None:
            current_shares = len(dbmetacluster.shares)
            if max_shares < current_shares:
                raise ArgumentError("%s has %d shares attached, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbmetacluster), current_shares,
                                     max_shares))
            dbmetacluster.max_shares = max_shares
            cluster_updated = True

        if comments is not None:
            dbmetacluster.comments = comments
            cluster_updated = True

        if high_availability is not None:
            dbmetacluster.high_availability = high_availability
            cluster_updated = True

        # TODO update_cluster_location would update VMs. Metaclusters
        # will contain VMs in Vulcan2 model.
        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)

        location_updated = update_cluster_location(session, logger,
                                          dbmetacluster,
                                          fix_location,
                                          plenaries, remove_plenaries,
                                          **arguments)

        if location_updated:
            cluster_updated = True

        if not cluster_updated:
            return

        session.add(dbmetacluster)
        session.flush()
        dbmetacluster.validate()

        plenary_info = Plenary.get_plenary(dbmetacluster, logger=logger)
        key = plenary_info.get_write_key()

        try:
            lock_queue.acquire(key)

            plenary_info.write(locked=True)
        except:
            plenary_info.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
