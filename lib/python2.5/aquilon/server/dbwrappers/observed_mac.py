# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a observed_mac simpler."""


from aquilon.aqdb.hw.observed_mac import ObservedMac


def get_or_create_observed_mac(session, dbswitch, port, mac):
    dbobserved_mac = session.query(ObservedMac).filter_by(
            switch=dbswitch, port_number=port, mac_address=mac).first()
    if dbobserved_mac:
        return dbobserved_mac
    dbobserved_mac = ObservedMac(switch=dbswitch, port_number=port,
                                 mac_address=mac)
    session.save(dbobserved_mac)
    return dbobserved_mac


