#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" For dsdb/sybase specific functionality and access"""

import os
import sys
import ms.version
from copy import copy
#from   ConfigParser import SafeConfigParser

ms.version.addpkg('sybase', '0.38-py25', 'dist')
import Sybase

from dispatch_table import dispatch_tbl as dt

class DsdbConnection(object):
    """ Wraps connections to DSDB """
    def __init__(self, fake=False, *args, **kw):

#TODO: failover support
        self.region = (os.environ.get('SYS_REGION') or None)
        if self.region == 'eu':
            self.dsn = 'LNP_DSDB11'
        elif self.region == 'hk':
            self.dsn = 'HKP_DSDB11'
        elif self.region == 'tk':
            self.dsn = 'TKP_DSDB11'
        else:
            self.dsn = 'NYP_DSDB11'
        assert self.dsn

        self.syb = Sybase.connect(self.dsn, 'dsdb_guest', 'dsdb_guest',
                                  'dsdb', datetime = 'auto', auto_commit = '0')
        assert self.syb._is_connected

    def run_query(self,sql):
        """Runs query sql. Note use runSybaseProc to call a stored procedure.
            Parameters:
                sql - SQL to run
            Returns:
                Sybase cursor object"""
        rs = self.syb.cursor()
        try:
           rs.execute(sql)
           return rs
        except Sybase.DatabaseError, e:
            print e

    def run_proc(self, proc, parameters):
        """Runs procedure with supplied parameters.
            Parameters:
                proc - Proc to call
                paramaters - List of parameters to the stored proc.
            Returns:
                Sybase cursor object"""
        rs = self.syb.cursor()
        try:              #not so sure we need all the fancyness
            rs.callproc(proc, parameters)
            return rs
        except Sybase.DatabaseError, e:
            print e
            #raise Sybase.DatabaseError(inst)
            #we're not raising this b/c it means you have
            #to import Sybase everywhere... reconsider this



    def dump(self, data_type, *args, **kw):
        sql = dt[data_type]

        if data_type == 'buildings_by_campus':
            campus=kw.pop('campus')
            if not campus:
                raise ValueError('buildings_by_campus requires campus kwarg')
            sql += "'%s'"% (campus)

        try:
            return self.run_query(sql).fetchall()
        except Exception,e:
            print e

    def get_network_by_sysloc(self,loc):
        """ append a sysloc to the base query, get networks"""
        #TODO: make it general case somehow
        s = "    AND location = '%s' \n    ORDER BY A.net_ip_addr"%(loc)
        sql = '\n'.join([dt['net_base'], s])

        data = self.run_query(sql)
        if data is not None:
            return data.fetchall()
        else:
            return None

    def get_host_pod(self,host):
        sql    = """
        SELECT boot_path FROM network_host A, bootparam B
        WHERE A.host_name   =  \'%s\'
          AND A.machine_id  =  B.machine_id
          AND B.boot_key    =  \'podname\'
          AND B.state       >= 0"""%(host)

        return self.run_query(sql).fetchall()[0][0]

    def close(self):
        self.syb.close()

if __name__ == '__main__':
    from pprint import pprint

    db = DsdbConnection()
    assert db

    print db.get_network_by_sysloc('np.ny.na')

    ops = ('country','city') #a few ones for testing

    for i in ops:
        print 'Dump(%s) from dsdb:\n%s\n'%(i, db.dump(i))

    host = 'cwipm1'
    print "getting host data for '%s'"%(host)
    print 'host %s is in the "%s" pod'%(host,db.get_host_pod(host))

    print 'buildings in ny campus:'
    pprint(db.dump('buildings_by_campus', campus='ny'), indent =4)
    print ' '


    db.close()
