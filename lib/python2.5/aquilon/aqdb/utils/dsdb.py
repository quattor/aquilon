#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" For dsdb/sybase specific functionality and access"""
import msversion
msversion.addpkg('sybase', '0.38-py25', 'dist')

import Sybase
import os

#TODO: for fun, put these into the database. select them out before running
# them to try on a *purely* data driven approach to programming. This could
# enable a brand new kind of "api" to aqd: one where the power user can
# create their own commands on the fly. (obviously we'd lock this down like
# CRAZY, but it could help people like Sam that know sql but don't know python
# for example)

get_country = """
    select country_symbol, country_name, continent
    from country where state >= 0
"""

get_campus = """
    select campus_name, comments from campus where state >= 0
"""

get_campus_entries = """
    select A.bldg_name, C.campus_name from bldg A, campus_entry B, campus C
        where A.bldg_id = B.bldg_id
        AND C.campus_id = B.campus_id
        AND A.state >= 0
        AND B.state >= 0
        AND C.state >= 0
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

get_bucket = """
    SELECT loc_name FROM loc_name WHERE state >= 0
    AND loc_name LIKE '%B%'
    AND loc_name NOT LIKE '%GLOBAL%'
    AND loc_name NOT LIKE '%pod%'
    ORDER BY loc_name """

get_network="""
    SELECT  net_name,
            net_ip_addr,
            abs(net_mask),
            isnull(net_type_id,0),
            SUBSTRING(location,CHAR_LENGTH(location) - 7,2) as sysloc,
            side, net_id FROM network
    WHERE state >= 0 """

get_net_type = """
    SELECT * FROM network_type """

host_info  = """ SELECT
    A.host_name,                                       /* network_host */
    B.cpu, B.virt_cpu, B.cputype, B.memory, B.hostid,  /* machine */
    C.name, C.version, C.kernel_id,                    /* os */
    D.maker, D.model, D.arch, D.karch,                 /* model */
    E.sys_loc, E.afscell --,                           /* minfo*/
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
           AND A.host_name = 'np3c1n4' """

class dsdb_connection(object):
    """ Wraps connections to DSDB """

    def __init__(self,*args, **kw):
        if os.environ['SYS_REGION'] == 'eu':
            self.dsn = 'LNP_DSDB11'
        else:
            self.dsn = 'NYP_DSDB11'

        if os.environ['USER'] == 'daqscott' and self.dsn == 'NYP_DSDB11':
            #print 'using kerberos authentication'
            principal = None
            for line in open('/ms/dist/syb/dba/files/sgp.dat').xreadlines():
                svr, principal = line.split()
                if svr == self.dsn:
                    break

            self.syb = Sybase.connect(self.dsn,'','','dsdb',
                                      delay_connect=1, datetime='auto')
            self.syb.set_property(Sybase.CS_SEC_NETWORKAUTH, Sybase.CS_TRUE)
            self.syb.set_property(Sybase.CS_SEC_SERVERPRINCIPAL, principal)
            self.syb.connect()
        else:
            #TODO: kuu to a user, then do the above
            self.syb = Sybase.connect(
                self.dsn, 'dsdb_guest', 'dsdb_guest', 'dsdb',
                datetime = 'auto', auto_commit = '0')

    def run_query(self,sql):
        """Runs query sql. Note use runSybaseProc to call a stored procedure.
            Parameters:
                sql - SQL to run
            Returns:
                Sybase cursor object"""
        rs = self.syb.cursor()
        rs.execute(sql)
        return rs

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
        except Sybase.DatabaseError, inst:
            print inst
            #we're not raising this b/c it means you have
            #to import Sybase everywhere...
            #raise Sybase.DatabaseError(inst)


def test():
    syb = dsdb_connection()
    sql    = """select boot_path from network_host A, bootparam B where
            A.host_name = \'blackcomb\'
            AND A.machine_id = B.machine_id
            AND B.boot_key = \'podname\'
            AND B.state >= 0"""
    foo = syb.run_query(sql)
    pod = foo.fetchall()[0][0]
    assert pod == 'eng.ny'
    print pod

def dump_campus():
    db = dsdb_connection()
    return db.run_query(get_campus).fetchall()

def dump_country():
    db = dsdb_connection()
    return db.run_query(get_country).fetchall()

def dump_city():
    db = dsdb_connection()
    return db.run_query(get_city).fetchall()

def dump_bldg():
    db = dsdb_connection()
    return db.run_query(get_bldg).fetchall()

def dump_bucket():
    db = dsdb_connection()
    return db.run_query(get_bucket).fetchall()

def dump_network():
    db = dsdb_connection()
    return db.run_query(get_network).fetchall()

def dump_net_type():
    db = dsdb_connection()
    return db.run_query(get_net_type).fetchall()

def esp():
    print
    db = dsdb_connection()
    return db.run_query(host_info).fetchall()

if __name__ == '__main__':
    #test()
    #a=esp()
    #print a[0]
    #a = dump_campus()
    a = dump_net_type()
    print a

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
