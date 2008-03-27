#!/ms/dist/python/PROJ/core/2.5.0/bin/python -W ignore
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

import msversion
msversion.addpkg('sybase', '0.38-py25', 'dist')
import Sybase

get_country=""" select country_symbol, country_name, continent
from country where state >= 0 """

def build_cache(obj_name):
    cache={}

    for c in s.query(obj_name).all():
        cache[str(c.name)]=c

    return cache

class aqsyb:
    '''Wraps connections and calls to sybase'''
    def __init__(self,dsn,database):
        principal = None
        for line in open('/ms/dist/syb/dba/files/sgp.dat').xreadlines():
            svr, principal = line.split()
            if svr == dsn:
                break
        print 'Using principal %s -> %s' % (svr, principal)

        self.syb = Sybase.connect(dsn,'','',database,delay_connect=1)
        self.syb.set_property(Sybase.CS_SEC_NETWORKAUTH, Sybase.CS_TRUE)
        self.syb.set_property(Sybase.CS_SEC_SERVERPRINCIPAL, principal)
        self.syb.connect()

        self.syb = Sybase.connect('NYP_DSDB11','dsdb_guest','dsdb_guest', \
                                  'dsdb',datetime='auto',auto_commit = '0')

    def run_query(self,sql):
        '''Runs query sql. Note use runSybaseProc to call a stored procedure.
            Parameters:
                sql - SQL to run
            Returns:
                Sybase cursor object'''
        rs = self.syb.cursor()
        rs.execute(sql)
        return rs

    def run_proc(self, proc, parameters):
        '''Runs procedure with supplied parameters.
            Parameters:
                proc - Proc to call
                paramaters - List of parameters to the stored proc.
            Returns:
                Sybase cursor object'''
        rs = self.syb.cursor()
        try:              #not so sure we need all the fancyness
            rs.callproc(proc, parameters)
            return rs
        except Sybase.DatabaseError, inst:
            print inst
            #we're not raising this all the way up yet b/c it means you have
            #to import Sybase everywhere...
            #raise Sybase.DatabaseError(inst)


if __name__ == '__main__':
    syb = aqsyb('NYP_DSDB11','dsdb')
    sql    = '''select boot_path from network_host A, bootparam B where
            A.host_name = \'blackcomb\'
            AND A.machine_id = B.machine_id
            AND B.boot_key = \'podname\'
            AND B.state >= 0'''
    foo = syb.run_query(sql)
    pod = foo.fetchall()[0][0]
    assert pod == 'eng.ny'
    print pod
