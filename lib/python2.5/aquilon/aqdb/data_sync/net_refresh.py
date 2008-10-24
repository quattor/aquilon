#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" to refresh network data from dsdb """

import os
import sys
import logging
import optparse

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
import aquilon.aqdb.depends

from sqlalchemy.exceptions      import DatabaseError, IntegrityError

#TODO: fix all the damn location imports with a shortcut in loc/__init__
from aquilon.aqdb.loc.hub       import Hub
from aquilon.aqdb.loc.city      import City
from aquilon.aqdb.loc.company   import Company
from aquilon.aqdb.loc.country   import Country
from aquilon.aqdb.loc.building  import Building
from aquilon.aqdb.loc.continent import Continent
from aquilon.aqdb.loc.location  import Location

#TODO: likewise, all the imports for system subtypes
from aquilon.aqdb.sy.system     import System
from aquilon.aqdb.sy.tor_switch import TorSwitch

from aquilon.aqdb.db_factory    import db_factory
from aquilon.aqdb.dsdb          import DsdbConnection
from aquilon.aqdb.net.network   import Network, _mask_to_cidr, get_bcast
from aquilon.aqdb.data_sync     import NetRecord
from aquilon.aqdb.data_sync     import RefreshReport

class NetRefresher(object):
    """ Class to encapsulate what's needed to replicate networks from AQDB
        to AQDB"""
    __shared_state = {}

    #Dependency injection: allows us to supply our own *fake* dsdb connection
    def __init__(self, dsdb_cnxn, session, *args, **kw):

        self.dsdb = dsdb_cnxn
        assert self.dsdb

        self.session = session
        assert self.session

        q = self.session.query(Building)
        self.location = q.filter_by(name=kw['bldg']).one()
        assert type(self.location) is Building

        self.report = RefreshReport()
        assert self.report

        self.log = logging.getLogger('net_refresh')
        assert self.log

        self.commit    = kw['commit']

    def _pull_dsdb_data(self, *args, **kw):
        """ loc argument is a sysloc string (DSDB stores this instead) """
        d = {}
        #query returns in order name, ip, mask, type_id, bldg, side
        for (name, ip, mask, type,
             bldg, side, dsdb_id) in self.dsdb.get_network_by_sysloc(
                                                    self.location.sysloc()):
            d[ip] = NetRecord(ip=ip, name=name, net_type=type,
                              mask=mask, bldg=bldg, side=side, dsdb_id=dsdb_id)
        return d

    def _pull_aqdb_data(self, *args, **kw):
        """ loc argument is a BUILDING CODE, different from dsdb """
        d = {}

        q = self.session.query(Network)
        for n in q.filter_by(location=self.location).all():
            d[n.ip] = n
        return d

    def _rollback(self, msg):
        """ a DRY method for error handling """
        self.log.error(msg)
        self.report.errs.append(msg)
        self.session.rollback()

    def refresh(self, *args, **kw):
        """ compares and refreshes the network table from dsdb to aqdb using
            sets makes computing union and delta of keys simple and succinct """

        self.log.debug('Starting network refresh')

        ds = self._pull_dsdb_data(*args, **kw)
        dset = set(ds.keys())

        aq = self._pull_aqdb_data(*args, **kw)
        aset = set(aq.keys())

        deletes  = aset - dset
        if deletes:
            self._do_deletes(deletes, aq, *args, **kw)
            aq = self._pull_aqdb_data(*args, **kw)
            aset = set(aq.keys())

        adds = dset - aset
        if adds:
            self._do_adds(adds, ds, *args, **kw)
            aq = self._pull_aqdb_data(*args, **kw)
            aset = set(aq.keys())

        compares = aset & dset
        if compares:
            self._do_updates(aset & dset , aq, ds, *args, **kw)

        self.log.debug('Finished network refresh logic')

    def _do_deletes(self, k, aq, *args, **kw):
        """ Deletes networks in aqdb and not in dsdb. It logs and handles
            associated reporting messages.

            arguments: list of keys and dict of aqdb networks to delete
            returns:   True/False on total success/a single failure """
            #TODO: revisit this ^^^
        for i in k:
            self.log.debug('deleting %s'%(aq[i]))
            self.report.dels.append(aq[i])

            if self.commit:
                try:
                    self.session.delete(aq[i])
                    self.session.commit()
                except IntegrityError,e:
#                    """ TODO: get records that connects back to the network and
#                            do something about it: delete it, or send message.
#                            enhancement: start marking objects for deletion and
#                            delete them after a week or two of no activity """
                    self._rollback(e)
                except Exception, e:
                    self._rollback(e)
                    continue

    def _do_adds(self, k, ds, *args, **kw):
        """ Adds networks in dsdb and not in aqdb. Handles the logging and
            job reporting along the way.

            arguments: list of keys (ip addresses) and dsdb NetRecords

            returns:   # of networks added or False based on total success or
                       a single failure """ #TODO: revisit this
        for i in k:
            try:
                c = _mask_to_cidr[ds[i].mask]
                net = Network(name         = ds[i].name,
                              ip           = ds[i].ip,
                              mask         = ds[i].mask,
                              cidr         = c,
                              bcast        = get_bcast(ds[i].ip, c),
                              network_type = ds[i].net_type,
                              side         = ds[i].side,
                              location     = self.location,
                              dsdb_id      = ds[i].dsdb_id)
                net.comments = getattr(ds[i], 'comments', None)
    #TODO: use a memoized query:
    #self.session.query(Building).filter_by(name=ds[i].bldg).one()
            except Exception, e:
                self.report.errs.append(e)
                self.log.error(e)
                continue

            #log here to get more detailed/uniform output
            self.log.debug('adding %s'%(net))
            self.report.adds.append(net)

            if self.commit:
                self.report.adds.append(net)
                try:
                    self.session.add(net)
                    self.session.commit()
                except Exception, e:
                    self._rollback(e)

    def _do_updates(self, k, aq, ds, *args, **kw):
        """ Makes changes to networks which have differences, logs/reports. We
            do this *VERY* cautiously with seperate try/except for everything

            arguments: list of keys (ip addresses) for networks present in both
                       data sources, plus a hash of the relevent data to compare

            returns:   # of networks successfully updated or False if there's a
                       single failure  """
        for i in k:
            if ds[i] != aq[i]:
                #get an updated version of the aqdb network
                try:
                    aq[i] = ds[i].update_aq_net(aq[i], self.log, self.report)
                except ValueError, e:
                    self.report.errs.append(e)
                    self.log.error(e)

                if self.commit:
                    try:
                        self.log.debug('trying to commit the update\n')
                        self.session.update(aq[i])
                        self.session.commit()
                        self.report.upds.append(ds[i].name)
                    except Exception, e:
                        self._rollback(e)

def main(*args, **kw):
    usage = """ usage: %prog [options]
    refreshes location data from dsdb to aqdb """

    desc = 'Synchronizes networks from DSDB to AQDB'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('-v',
                 action = 'count',
                 dest   = 'verbose',
                 default = 0,
                 help   = 'increase verbosity by adding more (vv), etc.')

    p.add_option('-b', '--building',
                 action = 'store',
                 dest   = 'building',
                 default = 'dd' )

    p.add_option('-n', '--dry-run',
                      action  = 'store_true',
                      dest    = 'dry_run',
                      default = False,
                      help    = "no commit (for testing, default=False)")
    opts, args = p.parse_args()

    dsdb = DsdbConnection()
    aqdb = db_factory()

    if opts.verbose > 1:
        log_level = logging.DEBUG
    elif opts.verbose > 0:
        log_level = logging.INFO
    else:
        log_level = logging.WARN

    logging.basicConfig(level=log_level,
                    format='%(asctime)s %(levelname)-6s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

    nr = NetRefresher(dsdb, aqdb.session(),
                      bldg=opts.building,
                      #keep logic stated in postive language (readability)
                      commit = not(opts.dry_run))
    nr.refresh()

    if opts.verbose < 2:
        #really verbose runs don't need reporting
        nr.report.display()


if __name__ == '__main__':
    main(sys.argv)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
