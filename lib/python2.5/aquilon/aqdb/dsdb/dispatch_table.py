dispatch_tbl={}

dispatch_tbl['country'] = """
    SELECT country_symbol, country_name, continent
        FROM country
        WHERE state >= 0
        ORDER BY country_symbol ASC"""

dispatch_tbl['campus'] = """
    SELECT campus_name, comments
        FROM campus
        WHERE state >= 0
        ORDER BY campus_name ASC"""

dispatch_tbl['campus_entries'] = """
    SELECT A.bldg_name, C.campus_name FROM bldg A, campus_entry B, campus C
        WHERE A.bldg_id = B.bldg_id
        AND C.campus_id = B.campus_id
        AND A.state >= 0
        AND B.state >= 0
        AND C.state >= 0 """

dispatch_tbl['buildings_by_campus'] = """
    SELECT A.bldg_name from bldg A, campus_entry B, campus C
    WHERE A.bldg_id = B.bldg_id
    AND B.campus_id = C.campus_id
    AND A.state >= 0
    AND B.state >= 0
    AND C.state >= 0
    AND C.campus_name = """

dispatch_tbl['city'] = """
    SELECT A.city_symbol, A.city_name, B.country_symbol
        FROM city A, country B
        WHERE A.country_id = B.country_id
        AND A.state >= 0
        AND B.state >= 0
        ORDER BY A.city_symbol ASC"""

dispatch_tbl['building'] = """
    SELECT A.bldg_name, A.bldg_addr, B.city_symbol FROM bldg A, city B
        WHERE A.city_id = B.city_id
        AND A.state >= 0
        AND B.state >= 0
        AND A.bldg_name != ' '
        ORDER BY A.bldg_name ASC """

dispatch_tbl['bucket'] = """
    SELECT loc_name FROM loc_name WHERE state >= 0
        AND loc_name LIKE '%B%'
        AND loc_name NOT LIKE '%GLOBAL%'
        AND loc_name NOT LIKE '%pod%'
        ORDER BY loc_name """

dispatch_tbl['net_base'] = """
    SELECT  A.net_name, A.net_ip_addr, abs(A.net_mask) as mask, B.network_type,
            SUBSTRING(location,CHAR_LENGTH(A.location) - 7,2) as sysloc,
            A.side, A.net_id FROM network A, network_type B
    WHERE A.net_ip_addr != '127.0.0.0'
    AND isnull(A.net_type_id,0) = B.network_type_id
    AND A.state >= 0 """ #removed net_id for now, it may not be needed in the new strategy

dispatch_tbl['network_full'] = dispatch_tbl['net_base']

#dispatch_tbl['city_by_bldg'] = """
#select A.city_symbol from city A, bldg B
#where A.city_id = B.city_id
#AND A.state >= 0
#AND B.state >= 0
#AND B.bldg_name = """

#    SELECT  net_name,
#            net_ip_addr,
#            abs(net_mask),
#            isnull(net_type_id,0),
#            SUBSTRING(location,CHAR_LENGTH(location) - 7,2) as sysloc,
#            side, net_id FROM network
#    WHERE
#    net_ip_addr != '127.0.0.0'
#    AND state >= 0  """

dispatch_tbl['np_network'] = ' '.join([dispatch_tbl['net_base'],
                                       "AND A.location like '%np.ny.na'"])
#"""
#    SELECT  net_name,
#            net_ip_addr,
#            abs(net_mask),
#            isnull(net_type_id,0),
#            SUBSTRING(location,CHAR_LENGTH(location) - 7,2) as sysloc,
#            side, net_id FROM network
#    WHERE state >= 0
#    AND net_ip_addr != '127.0.0.0'
#    AND location like '%np.ny.na' """

dispatch_tbl['net_ids'] = """
SELECT net_id FROM network WHERE net_ip_addr != '127.0.0.0' AND state >= 0 """

dispatch_tbl['net_type'] = """
    SELECT * FROM network_type """

dispatch_tbl['sapphire_bldgs'] = """
    SELECT bldg_name FROM bldg WHERE bldg_id in (
        SELECT bldg_id FROM campus_entry A, campus B WHERE
        A.campus_id = B.campus_id
        AND B.campus_name = 'vi'
        AND A.state >=0
        AND B.state >=0) """

#TODO: make this a template string and have the dump method work it out
dispatch_tbl['host_info']  = """ SELECT
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
           AND A.host_name = 'HOST' """

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
