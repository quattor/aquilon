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
"""

# NOTE: the network_type tables id #'s actually match up with dsdb's
# network_type table's id column, so we just import it directly for speed.
get_network = """
    SELECT  A.net_name, A.net_ip_addr, A.net_ip_value, A.net_mask, A.byte_mask,
    isnull(net_type_id,4),
    SUBSTRING(A.location,CHAR_LENGTH(A.location) - 7,2) as sysloc, A.side,
    B.campus_name, C.bucket_name
    FROM network A, campus B, bucket C
    WHERE A.campus_id *= B.campus_id
    AND A.bucket_id *= C.bucket_id
    AND A.state >=0
    AND B.state >=0
    AND C.state >=0
"""

class aqsyb:
    '''Wraps connections and calls to sybase'''
    def __init__(self,data_src):
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


def test():
    syb = aqsyb('RO_PROD')
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
    db = aqsyb('RO_PROD')
    return db.run_query(get_country).fetchall()

def dump_city():
    db = aqsyb('RO_PROD')
    return db.run_query(get_city).fetchall()

def dump_bldg():
    db = aqsyb('RO_PROD')
    return db.run_query(get_bldg).fetchall()

def dump_network():
    db = aqsyb('RO_PROD')
    return db.run_query(get_network).fetchall()

if __name__ == '__main__':
    test()
    #country()
