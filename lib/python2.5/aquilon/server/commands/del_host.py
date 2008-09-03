#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del host`."""


import os

from threading import Lock
from twisted.python import log
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.host import (hostname_to_host, get_host_dependencies)
from aquilon.server.processes import (DSDBRunner, build_index)
from aquilon.server.templates.host import PlenaryHost

delhost_lock = Lock()


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    def render(self, session, hostname, user, **arguments):
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

        log.msg("Aquiring lock to attempt to delete %s" % hostname)
        delhost_lock.acquire()
        try:
            log.msg("Aquired lock, attempting to delete %s" % hostname)
            # Check dependencies, translate into user-friendly message
            dbhost = hostname_to_host(session, hostname)
            builddir = os.path.join(self.config.get("broker", "builddir"), "domains", dbhost.domain.name, "profiles")
            ph = PlenaryHost(dbhost)
            domain = dbhost.domain.name
            fqdn   = dbhost.fqdn
            session.refresh(dbhost)
            deps = get_host_dependencies(session, dbhost)
            if (len(deps) != 0):
                deptext = "\n".join(["  %s"%d for d in deps])
                raise ArgumentError("cannot delete host '%s' due to the following dependencies:\n%s"%(hostname, deptext))

            # Hack to make sure the machine object is refreshed in future queries.
            archetype = dbhost.archetype.name
            dbmachine = dbhost.machine
            session.refresh(dbmachine)
            ip = None
            for interface in dbmachine.interfaces:
                if interface.bootable:
                    ip = interface.ip
            if not ip and archetype != 'aurora':
                raise ArgumentError("No boot interface found for host to delete from dsdb.")
    
            for template in dbhost.templates:
                log.msg("Before deleting host '%s', removing template '%s'"
                        % (fqdn, template.cfg_path))
                session.delete(template)

            session.delete(dbhost)
            session.flush()
            delplenary = True
    
            if archetype != 'aurora':
                try:
                    dsdb_runner = DSDBRunner()
                    dsdb_runner.delete_host_details(ip)
                except ProcessException, e:
                    raise ArgumentError("Could not remove host %s from dsdb: %s" %
                            (hostname, e))

            session.refresh(dbmachine)
        finally:
            log.msg("Released lock from attempt to delete %s" % hostname)
            delhost_lock.release()

        # Only if we got here with no exceptions do we clean the template
        if (delplenary):
            ph.remove(builddir)
            profiles = self.config.get("broker", "profilesdir")

            # subsidiary cleanup for hygiene
            # (we don't actually care if these fail, since it doesn't break anything)
            qdir = self.config.get("broker", "quattordir")
            for file in [
                os.path.join(self.config.get("broker", "depsdir"), domain, fqdn+".dep"),
                os.path.join(profiles, fqdn+".xml"),
                os.path.join(qdir, "build", "xml", domain, fqdn+".xml"),
                os.path.join(qdir, "build", "xml", domain, fqdn+".xml.dep")
                ]:
                try:
                    os.remove(file)
                except:
                    pass
            build_index(self.config, session, profiles)

        return


#if __name__=='__main__':
