# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
"""Wrapper to make getting a observed_mac simpler."""


from aquilon.aqdb.model import ObservedMac


def update_or_create_observed_mac(session, dbnetdev, port, mac, now):
    dbobserved_mac = session.query(ObservedMac).filter_by(
        network_device=dbnetdev, port=port, mac_address=mac).first()
    if dbobserved_mac:
        dbobserved_mac.last_seen = now
        return dbobserved_mac
    # Set creation_date explicitely instead of relying on the default to ensure
    # creation_date == last_seen
    dbobserved_mac = ObservedMac(network_device=dbnetdev, port=port,
                                 mac_address=mac, creation_date=now,
                                 last_seen=now)
    session.add(dbobserved_mac)
    return dbobserved_mac
