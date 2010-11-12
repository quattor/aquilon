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
"""Contains the logic for `aq del host`."""


import os

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_dependencies)
from aquilon.server.processes import (DSDBRunner, remove_file)
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.templates.index import build_index
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.locks import lock_queue, DeleteKey, CompileKey


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, user, **arguments):
        # removing the plenary host requires a compile lock, however
        # we want to avoid deadlock by the fact that we're messing
        # with two locks here, so we want to be careful. We grab the
        # plenaryhost early on (in order to get the filenames filled
        # in from the db info before we delete it from the db. We then
        # hold onto those references until we've completed the db
        # cleanup and if all of that is successful, then we delete the
        # plenary file (which doesn't require re-evaluating any stale
        # db information) after we've released the delhost lock.
        delplenary = False

        # Any service bindings that we need to clean up afterwards
        bindings = PlenaryCollection()
        key = DeleteKey("system", logger=logger)
        try:
            lock_queue.acquire(key)
            # Check dependencies, translate into user-friendly message
            dbhost = hostname_to_host(session, hostname)
            ph = PlenaryHost(dbhost, logger=logger)
            domain = dbhost.branch.name
            deps = get_host_dependencies(session, dbhost)
            if (len(deps) != 0):
                deptext = "\n".join(["  %s"%d for d in deps])
                raise ArgumentError("Cannot delete host %s due to the "
                                    "following dependencies:\n%s." %
                                    (hostname, deptext))

            archetype = dbhost.archetype.name
            dbmachine = dbhost.machine
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

            ip = dbmachine.primary_ip
            fqdn = dbmachine.fqdn

            for binding in dbhost.services_used:
                ### WARNING ###
                si = binding.service_instance
                if si:
                    plenary = PlenaryServiceInstanceServer(si.service, si,
                                                           logger=logger)
                    bindings.append(plenary)
                logger.info("Before deleting host '%s', removing binding '%s'"
                            % (fqdn, binding.cfg_path))

            del dbhost.services_used[:]

            # In case of Zebra, the IP may be configured on multiple interfaces
            for iface in dbmachine.interfaces:
                if ip in iface.addresses:
                    iface.addresses.remove(ip)

            session.delete(dbhost)
            session.delete(dbmachine.primary_name)
            session.flush()
            session.expire(dbmachine)
            delplenary = True

            if archetype != 'aurora' and ip is not None:
                try:
                    dsdb_runner = DSDBRunner(logger=logger)
                    dsdb_runner.update_host(dbmachine, oldinfo)
                except ProcessException, e:
                    raise ArgumentError("Could not remove host %s from "
                                        "DSDB: %s" % (hostname, e))

            # Past the point of no return... commit the transaction so
            # that we can free the delete lock.
            session.commit()
        finally:
            lock_queue.release(key)

        # Only if we got here with no exceptions do we clean the template
        # Trying to clean up after any errors here is really difficult
        # since the changes to dsdb have already been made.
        if (delplenary):
            key = ph.get_remove_key()
            key = CompileKey.merge([key, bindings.get_write_key()])
            try:
                lock_queue.acquire(key)
                ph.cleanup(domain, locked=True)
                # And we also want to remove the profile itself
                profiles = self.config.get("broker", "profilesdir")
                # Only one of these should exist, but it doesn't hurt
                # to try to clean up both.
                xmlfile = os.path.join(profiles, fqdn + ".xml")
                remove_file(xmlfile, logger=logger)
                xmlgzfile = xmlfile + ".gz"
                remove_file(xmlgzfile, logger=logger)
                # And the cached template created by ant
                remove_file(os.path.join(self.config.get("broker",
                                                         "quattordir"),
                                         "objects", fqdn + ".tpl"),
                            logger=logger)
                bindings.write(locked=True)
            finally:
                lock_queue.release(key)

            build_index(self.config, session, profiles, logger=logger)

        return
