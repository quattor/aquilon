#!/ms/dist/python/PROJ/core/2.5.0/bin/python
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

import os

get_country = """
    select country_symbol, country_name, continent
    from country where state >= 0
"""
get_city = """
    select A.city_symbol, A.city_name, B.country_symbol
    from city A, country B
    where A.country_id = B.country_id
    AND A.state >= 0
    AND B.state >= 0
"""

get_bldg = """
    select A.bldg_name, A.bldg_addr, B.city_symbol from bldg A, city B
    where A.city_id = B.city_id
    AND A.state >= 0
    AND B.state >= 0
    AND A.bldg_name != ' '
"""

#get_bucket = "select lower(bucket_name), comments from bucket where state >= 0"
get_bucket = """
    SELECT loc_name FROM loc_name WHERE state >= 0
    AND loc_name LIKE '%B%'
    AND loc_name NOT LIKE '%GLOBAL%'
    AND loc_name NOT LIKE '%pod%'
    ORDER BY loc_name """

# NOTE: the network_type tables id #'s actually match up with dsdb's
# network_type table's id column, so we just import it directly for speed.
get_network = """
    SELECT  A.net_name, A.net_ip_addr, abs(A.net_ip_value), abs(A.net_mask),
    abs(A.byte_mask), isnull(net_type_id,4),
    SUBSTRING(A.location,CHAR_LENGTH(A.location) - 7,2) as sysloc, A.side,
    B.campus_name, C.bucket_name
    FROM network A, campus B, bucket C
    WHERE A.campus_id *= B.campus_id
    AND A.bucket_id *= C.bucket_id
    AND A.state >=0
    AND B.state >=0
    AND C.state >=0
"""
host_info  = """
SELECT
        A.host_name,                                          /* network_host */
        B.cpu, B.virt_cpu, B.cputype, B.memory, B.hostid,          /* machine */
        C.name, C.version, C.kernel_id,                                 /* os */
        D.maker, D.model, D.arch, D.karch,                          /* model */
        E.sys_loc, E.afscell --,                               /* minfo*/
        --G.iface_name, G.ip_addr, G.ether_addr            /* interface info */


                FROM   network_host A, machine B, os C, model D, machine_info E
                --, network_iface G

                WHERE  A.name_type = 0
                       AND A.machine_id = B.machine_id
                       AND B.primary_host_id = A.host_id
                       AND B.os_id *= C.id
                       AND B.model_id *= D.id
                       AND B.machine_id = E.machine_id
                       --AND B.machine_id *= G.machine_id


                       AND A.state >= 0
                       AND B.state >= 0
                       AND C.state >= 0
                       AND D.state >= 0
                       AND E.state >= 0
                       --AND G.state >= 0

                       and A.host_name = 'np3c1n4'

"""


class aqsyb:
    '''Wraps connections and calls to sybase'''
    def __init__(self,dsn,database):
        if os.environ['USER'] == 'daqscott':
            #print 'using kerberos authentication'
            principal = None
            for line in open('/ms/dist/syb/dba/files/sgp.dat').xreadlines():
                svr, principal = line.split()
                if svr == dsn:
                    break

            self.syb = Sybase.connect(dsn,'','',database,
                                      delay_connect=1, datetime='auto')
            self.syb.set_property(Sybase.CS_SEC_NETWORKAUTH, Sybase.CS_TRUE)
            self.syb.set_property(Sybase.CS_SEC_SERVERPRINCIPAL, principal)
            self.syb.connect()
        else:
            #TODO: kuu to a user, then do the above
            self.syb = Sybase.connect(dsn,'dsdb_guest','dsdb_guest', \
                                  database,datetime='auto',auto_commit = '0')

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
            #we're not raising this b/c it means you have
            #to import Sybase everywhere...
            #raise Sybase.DatabaseError(inst)


def test():
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

def dump_country():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(get_country).fetchall()

def dump_city():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(get_city).fetchall()

def dump_bldg():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(get_bldg).fetchall()

def dump_bucket():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(get_bucket).fetchall()

def dump_network():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(get_network).fetchall()

def esp():
    db = aqsyb('NYP_DSDB11','dsdb')
    return db.run_query(host_info).fetchall()

if __name__ == '__main__':
    #test()
    a=esp()
    print a[0]
