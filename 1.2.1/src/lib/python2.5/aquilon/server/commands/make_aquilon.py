#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq make aquilon`."""


from os import path as os_path, environ as os_environ
from tempfile import mkdtemp

from aquilon.exceptions_ import ProcessException, DetailedProcessException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.cfg_path import get_cfg_path
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.service_instance import choose_service_instance
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.server.templates import PlenaryMachineInfo
from aquilon.server.processes import (run_command, remove_dir, 
        read_file, build_index)


class CommandMakeAquilon(BrokerCommand):

    required_parameters = ["hostname", "os", "personality"]

    @add_transaction
    @az_check
    def render(self, session, hostname, os, personality, user, **arguments):
        dbhost = hostname_to_host(session, hostname)
        # Currently, for the Host to be created it *must* be associated with
        # a Machine already.  If that ever changes, need to check here and
        # bail if dbhost.machine does not exist.

        # Need to get all the BuildItem objects for this host.
        # They should include:
        # - exactly one OS
        # - exactly one personality
        # And may include:
        # - many services
        # - many features?

        if os:
            dbos = get_cfg_path(session, "os", os)
            dbos_bi = session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=dbos.tld).first()
            if dbos_bi:
                dbos_bi.cfg_path = dbos
            else:
                # FIXME: This could fail if there is already an item at 0
                dbos_bi = BuildItem(host=dbhost, cfg_path=dbos, position=0)
            session.save_or_update(dbos_bi)

        if personality:
            dbpersonality = get_cfg_path(session, "personality", personality)
            dbpersonality_bi = session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=dbpersonality.tld).first()
            if dbpersonality_bi:
                dbpersonality_bi.cfg_path = dbpersonality
            else:
                # FIXME: This could fail if there is already an item at 1
                dbpersonality_bi = BuildItem(host=dbhost,
                        cfg_path=dbpersonality, position=1)
            session.save_or_update(dbpersonality_bi)

        session.flush()
        session.refresh(dbhost)
        dbservice_tld = session.query(Tld).filter_by(type='service').one()
        for item in dbhost.archetype.service_list:
            dbservice_bi = session.query(BuildItem).filter_by(
                    host=dbhost).join('cfg_path').filter_by(
                    tld=dbservice_tld).filter(CfgPath.relative_path.like(
                    item.service.name + '/%')).first()
            if dbservice_bi:
                continue
            dbinstance = choose_service_instance(session, dbhost, item.service)
            dbservice_bi = BuildItem(host=dbhost, cfg_path=dbinstance.cfg_path,
                    position=3)
            dbhost.templates.append(dbservice_bi)
            dbhost.templates._reorder()
            session.save(dbservice_bi)

        session.flush()
        session.refresh(dbhost)
        session.refresh(dbhost.machine)

        tempdir = mkdtemp()
        plenary_info = PlenaryMachineInfo(dbhost.machine)
        plenary_info.reconfigure(dbhost, tempdir,
                self.config.get("broker", "servername"), user)

        filename = os_path.join(tempdir, dbhost.fqdn) + '.tpl'
        domaindir = os_path.join(self.config.get("broker", "templatesdir"),
                dbhost.domain.name)
        archetypedir = os_path.join(domaindir, dbhost.archetype.name)
        includes = [archetypedir, domaindir,
                self.config.get("broker", "plenarydir"),
                self.config.get("broker", "swrepdir")]
        outfile = os_path.join(tempdir, dbhost.fqdn + '.xml')
        outdep = outfile + '.dep'  # Yes, this ends with .xml.dep
        panc_env={"PATH":"%s:%s" % (self.config.get("broker", "javadir"),
            os_environ.get("PATH", ""))}
        args = [self.config.get("broker", "panc")]
        for include in includes:
            args.append('-I')
            args.append(include)
        args.append('-y')
        args.append('-x')
        args.append('xmldb')
        args.append(filename)
        try:
            run_command(args, env=panc_env, path=tempdir)
        except ProcessException, e:
            input = ""
            if os_path.exists(filename):
                input = file(filename).read()
            output = e.out
            if not output and os_path.exists(outfile):
                output = file(outfile).read()
            raise DetailedProcessException(e, input, output)
        profilesdir = self.config.get("broker", "profilesdir")
        run_command(["cp", outfile, profilesdir])
        run_command(["cp", outdep, self.config.get("broker", "depsdir")])
        run_command(["cp", filename, self.config.get("broker", "hostsdir")])
        build_index(self.config, session, profilesdir)
        remove_dir(tempdir)
        return


#if __name__=='__main__':
