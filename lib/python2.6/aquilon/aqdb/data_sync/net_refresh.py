#!/usr/bin/env python2.6
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
""" to refresh network data from dsdb """

import os
import sys
import logging
import optparse
import math
from ipaddr import IPv4Address, IPv4Network

if __name__ == "__main__":
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy.exceptions import DatabaseError, IntegrityError
from sqlalchemy.sql.expression import asc

from aquilon.aqdb.model import Building, System, Network
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.dsdb import DsdbConnection
from aquilon.aqdb.data_sync.net_record import NetRecord

LOGGER = logging.getLogger('aquilon.aqdb.data_sync.net_refresh')


class NetRefresher(object):
    """Encapsulate what's needed to replicate networks from DSDB to AQDB"""
    __shared_state = {}

    #Dependency injection: allows us to supply our own *fake* dsdb connection
    def __init__(self, dsdb_cnxn, session,
                 logger=LOGGER, loglevel=logging.INFO,
                 bldg=None, incremental=False, dryrun=False):
        """If no building is set all locations will be synchronized.

        Set incremental to True to commit every change individually.  This
        will ensure that any errors do not roll back the entire process.

        Set dryrun to True to flush every change.  No change will
        actually be committed.  This can help to pinpoint groups of
        errors instead of failing on the first.

        """

        self.dsdb = dsdb_cnxn
        assert self.dsdb

        self.session = session
        assert self.session

        if bldg:
            self.location = Building.get_unique(session, bldg,
                                                compel=ValueError)
            assert type(self.location) is Building
        else:
            self.location = None

        self.errors = []

        self.log = logger
        assert self.log
        # Let the caller choose the default log level and wrap for convenience.
        self.loglevel = loglevel
        self.info = lambda *args, **kwargs: self.log.log(self.loglevel,
                                                         *args, **kwargs)

        self.incremental = incremental
        self.dryrun = dryrun

    def _pull_dsdb_data(self):
        d = {}
        if self.location:
            data = self.dsdb.get_network_by_sysloc(self.location.sysloc())
        else:
            data = self.dsdb.dump('net_base')
        buildings = {}
        for building in self.session.query(Building).all():
            buildings[building.name] = building
        for (name, ip, mask, type, bldg, side) in data:
            prefixlen = 32 - int(math.log(mask, 2))
            ip = IPv4Address(ip)
            d[ip] = NetRecord(ip=ip, name=name, net_type=type,
                              cidr=prefixlen, side=side, bldg=bldg,
                              location=buildings.get(bldg, None))
        return d

    def _pull_aqdb_data(self):
        # Note that a query will auto-flush first...
        d = {}
        q = self.session.query(Network)
        if self.location:
            q = q.filter_by(location=self.location)
        for n in q.all():
            d[n.ip] = n
        return d

    def refresh(self):
        self.log.debug('Starting network refresh')
        self.session.autoflush = False
        self._refresh_networks()
        # This will be a no-op if self.incremental or self.dryrun is True
        self.session.flush()
        self._refresh_system_networks()
        self.log.debug('Finished network refresh')

    def _refresh_networks(self):
        """Compares and refreshes the network table from dsdb to aqdb.

        Using sets makes computing union and delta of keys simple and succinct.

        """
        ds = self._pull_dsdb_data()
        dset = set(ds.keys())

        aq = self._pull_aqdb_data()
        aset = set(aq.keys())

        deletes = aset - dset
        if deletes:
            self._do_deletes(deletes, aq)
            aq = self._pull_aqdb_data()
            aset = set(aq.keys())

        adds = dset - aset
        if adds:
            self._do_adds(adds, ds)
            aq = self._pull_aqdb_data()
            aset = set(aq.keys())

        compares = aset & dset
        if compares:
            self._do_updates(aset & dset, aq, ds)

    def _error(self, msg):
        self.log.error(msg)
        self.errors.append(msg)

    def _commit(self, msg):
        self.info(msg)
        try:
            if self.dryrun:
                self.session.flush()
            if self.incremental:
                self.session.commit()
        except Exception, e:
            self._error("Error %s: %s" % (msg, e))
            # This doesn't do the right thing on a dryrun (goes back to
            # a clean slate instead of the last success), but hopefully
            # close enough.
            self.session.rollback()
            return False
        return True

    def _do_deletes(self, k, aq):
        """Deletes networks in aqdb and not in dsdb.

        arguments: list of keys and dict of aqdb networks to delete

        """
        for i in k:
            self.session.delete(aq[i])
            self._commit('deleting {0}'.format(aq[i]))

    def _do_adds(self, k, ds):
        """Adds networks in dsdb and not in aqdb.

        arguments: list of keys (ip addresses) and dsdb NetRecords

        """
        for i in k:
            if not ds[i].location:
                msg = "Not adding network %s: " % ds[i].ip
                if not ds[i].bldg:
                    self.log.warn(msg + "missing building information in dsdb")
                else:
                    self._error(msg + "building %s missing in aqdb" %
                                ds[i].bldg)
                continue
            net = Network(name=ds[i].name,
                          network=IPv4Network("%s/%s" % (ds[i].ip, ds[i].cidr)),
                          network_type=ds[i].net_type,
                          side=ds[i].side,
                          location=ds[i].location)

            net.comments = getattr(ds[i], 'comments', None)

            self.session.add(net)
            self._commit('adding {0}'.format(net))

    def _do_updates(self, k, aq, ds):
        """Makes changes to networks which have differences.

        arguments: list of keys (ip addresses) for networks present in both
                   data sources, plus a hash of the relevent data to compare

        """
        for i in k:
            if not ds[i].location:
                msg = "Not updating network %s: " % ds[i].ip
                if not ds[i].bldg:
                    self.log.warn(msg + "missing building information in dsdb")
                else:
                    self._error(msg + "building %s missing in aqdb" %
                                ds[i].bldg)
                continue
            if ds[i] != aq[i]:
                #get an updated version of the aqdb network
                aq[i] = ds[i].update_aq_net(aq[i], self)
                self.session.add(aq[i])
                self._commit('saving {0}'.format(aq[i]))
                # Each update has already been added to the report.

    def _refresh_system_networks(self):
        """Validate network entries for stored IPs."""
        # Note... I couldn't think of a good way to "restrict" this algorithm
        # to a single building efficiently and correctly.

        # When we switch to the new DNS schema it should be sufficient
        # to swap this to ARecord and call it a day.  (Unless IP/network
        # combos are also stashed away somewhere else.)
        q = self.session.query(System)
        q = q.filter(System.ip != None)
        q = q.order_by(asc(System.ip))
        systems = q.all()

        q = self.session.query(Network)
        q = q.order_by(asc(Network.ip))
        networks = q.all()

        def set_network(s, n):
            if s.network != n:
                s.network = n
                self.session.add(s)
                self._commit('updating %s [%s] with network %s' %
                             (s.fqdn, s.ip, n.ip))

        s_index = 0
        n_index = 0
        # Iterate through the ordered lists matching systems to their networks.
        # Not worried about the edge cases of no networks or no systems.  If
        # there are no systems there is nothing to fix.  If there are no
        # networks then all the systems are pointing at null anyway.
        while(s_index < len(systems) and n_index < len(networks)):
            # database objects
            sys = systems[s_index]
            net = networks[n_index]
            # Hopefully the common case... our system IP is in the range
            # of the current network.  Make sure the network is set
            # appropriately and move on to the next system.
            if sys.ip in net.network:
                set_network(sys, net)
                s_index += 1
                continue
            # Our system is beyond the range of the current network, so
            # proceed to checking against the next network.
            if sys.ip > net.broadcast:
                n_index += 1
                continue
            # At this point we know our system is not in the range of
            # any networks.  We started at the "lowest" network and
            # have been working up.  Since the system IP is less than
            # the network IP we can't expect incrementing to the next
            # network to help us find one. :)
            self._error('No network found for IP address %s [%s].' %
                        (sys.ip, sys.fqdn))
            set_network(sys, None)
            s_index += 1
            continue

def main(*args, **kw):
    usage = """ usage: %prog [options]
    refreshes location data from dsdb to aqdb """

    desc = 'Synchronizes networks from DSDB to AQDB'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('-v',
                 action='count',
                 dest='verbose',
                 default=0,
                 help='increase verbosity by adding more (vv), etc.')

    p.add_option('-b', '--building',
                 action='store',
                 dest='building',
                 default=None)

    p.add_option('-i', '--incremental',
                 action='store_true',
                 dest='incremental',
                 default=False,
                 help="commit every change immediately instead of batching")

    p.add_option('-n', '--dry-run',
                 action='store_true',
                 dest='dry_run',
                 default=False,
                 help="no commit (for testing, default=False)")
    opts, args = p.parse_args()

    dsdb = DsdbConnection()
    aqdb = DbFactory()

    if opts.verbose > 1:
        log_level = logging.DEBUG
    elif opts.verbose > 0:
        log_level = logging.INFO
    else:
        log_level = logging.WARN

    logging.basicConfig(level=log_level,
                    format='%(asctime)s %(levelname)-6s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

    session = aqdb.Session()
    nr = NetRefresher(dsdb, session,
                      bldg=opts.building,
                      incremental=opts.incremental,
                      dryrun=opts.dry_run)
    nr.refresh()

    if opts.dry_run:
        session.rollback()
    else:
        session.commit()

    # Raise on nr.errors?

if __name__ == '__main__':
    main(sys.argv)
