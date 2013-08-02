#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" For dsdb/sybase specific functionality and access"""

import os
import ms.version

ms.version.addpkg('sybase', '0.39-ms1-15.0.0.17')
import Sybase

from dispatch_table import dispatch_tbl as dt


class DsdbConnection(object):
    """ Wraps connections to DSDB """
    def __init__(self, fake=False, *args, **kw):

        self.region = (os.environ.get('SYS_REGION') or None)
        if self.region == 'eu':
            self.dsn = 'LNP_DSDB11'
        elif self.region == 'hk':
            self.dsn = 'HKP_DSDB11'
        elif self.region == 'tk':
            self.dsn = 'TKP_DSDB11'
        else:
            self.dsn = 'NYP_DSDB11'
        assert self.dsn, "Cannot determine DSDB instance to use for region %s" % self.region

        self.syb = Sybase.connect(self.dsn, 'dsdb_guest', 'dsdb_guest',
                                  'dsdb', auto_commit='0')
        assert self.syb._is_connected, "Cannot connect to %s" % self.dsn

    def run_query(self, sql, limit=None):
        """ Runs query sql. Note use runSybaseProc to call a stored procedure.
            Parameters:
                sql - SQL to run
                limit - number of rows to return (default=None)
            Returns:
                Sybase cursor object """

        if isinstance(limit, int):
            sql = 'SET ROWCOUNT %i %s SET ROWCOUNT 0' % (limit, sql)

        rs = self.syb.cursor()
        try:
            rs.execute(sql)
            return rs
        except Sybase.DatabaseError, e:
            print e

    def run_proc(self, proc, parameters):
        """ Runs a stored procedure with supplied parameters.
            Parameters:
                proc - Proc to call
                paramaters - List of parameters to the stored proc.
            Returns:
                Sybase cursor object """
        rs = self.syb.cursor()
        try:  # not so sure we need all the fancyness
            rs.callproc(proc, parameters)
            return rs
        except Sybase.DatabaseError, e:
            print e

    def dump(self, data_type, limit=None, *args, **kw):
        sql = dt[data_type]

        if data_type == 'buildings_by_campus':
            campus = kw.pop('campus')
            if not campus:
                raise ValueError('buildings_by_campus requires campus kwarg')
            sql += "'%s'" % campus

        return self.run_query(sql, limit).fetchall()

    def get_network_by_sysloc(self, loc):
        """ append a sysloc to the base query, get networks """
        s = "    AND location = '%s' \n    ORDER BY A.net_ip_addr" % (loc)
        sql = '\n'.join([dt['net_base'], s])

        data = self.run_query(sql)
        return data.fetchall() if data else None

    def get_host_pod(self, host):
        sql = """
        SELECT boot_path FROM network_host A, bootparam B
        WHERE A.host_name   =  \'%s\'
          AND A.machine_id  =  B.machine_id
          AND B.boot_key    =  \'podname\'
          AND B.state       >= 0""" % host

        return self.run_query(sql).fetchall()[0][0]

    def close(self):
        self.syb.close()


def test():  # pragma: no cover
    db = DsdbConnection()
    assert db, "No dsdb connection"

    #print db.get_network_by_sysloc('np.ny.na')

    #ops = ('country','city') #a few ones for testing

    #for i in ops:
    #    print 'Dump(%s) from dsdb:\n%s\n'%(i, db.dump(i))

    #host = 'cwipm1'
    #print "getting pod of '%s'"%(host)
    #print 'host %s is in the "%s" pod'%(host,db.get_host_pod(host))

    #print 'buildings in ny campus:'
    #print db.dump('buildings_by_campus', campus='ny')
    #print ' '
    from pprint import pprint
    pprint(db.dump('transaction_log'))

    db.close()

if __name__ == '__main__':
    test()  # for now
