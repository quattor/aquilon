# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Wrappers for GRN handling"""

import os.path
from csv import DictReader

try:
    import cdb
except ImportError:
    _has_cdb = False
else:
    _has_cdb = True

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Grn
from aquilon.worker.locks import SyncKey


def lookup_autoupdate(datadir, session, logger, grn, eon_id):
    # Check the CDB file first, since that quickly tells us if the cache is
    # stale or if just the input is wrong
    if grn:
        name = os.path.join(datadir, "eon_catalog_by_name.cdb")
        key = grn
    else:
        name = os.path.join(datadir, "eon_catalog_by_id.cdb")
        key = str(eon_id)

    cdb_file = cdb.init(name)  # pylint: disable=E1101
    # Tell pep8 not to warn about .has_key()
    if not cdb_file.has_key(key.encode("ascii")):  # noqa
        return None

    # We found a GRN which is not in the DB. Pefrorm a full refresh, because it
    # is quick enough.
    with SyncKey(data="grn", logger=logger):
        # Try again in case a concurrent process have already updated the cache
        # by the time we got the lock
        dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
        if dbgrn:  # pragma: no cover
            return dbgrn

        update_grn_map(datadir, session, logger)
        dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
    return dbgrn


def lookup_grn(session, grn=None, eon_id=None, usable_only=True, logger=None,
               config=None, autoupdate=True):
    dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
    if not dbgrn and autoupdate and _has_cdb:
        if not config.has_option("broker", "grn_to_eonid_map_location"):
            return None

        datadir = config.get("broker", "grn_to_eonid_map_location")
        dbgrn = lookup_autoupdate(datadir, session, logger, grn, eon_id)

    if not dbgrn:
        if grn:
            raise NotFoundException("GRN %s not found." % grn)
        else:
            raise NotFoundException("EON ID %s not found." % eon_id)

    if usable_only and dbgrn.disabled:
        raise ArgumentError("GRN %s is not usable for new systems." % dbgrn.grn)

    return dbgrn


def update_grn_map(datadir, session, logger):

    q = session.query(Grn)
    grns = {dbgrn.eon_id: dbgrn for dbgrn in q}

    name = os.path.join(datadir, "eon_catalog.csv")
    added = 0
    updated = 0
    deleted = 0
    with open(name) as f:
        reader = DictReader(f)
        for row in reader:
            changed = False
            eon_id = int(row["id"])
            disabled = int(row["can_map_resources"]) == 0 or \
                int(row["deleted"]) != 0

            if eon_id not in grns:
                if not row["name"]:
                    logger.info("EON ID %d has no name, ignoring" % eon_id)
                    continue

                dbgrn = Grn(eon_id=eon_id, grn=row["name"], disabled=disabled)
                session.add(dbgrn)
                added += 1
            else:
                dbgrn = grns[eon_id]
                # Mark it as processed
                del grns[eon_id]

            if dbgrn.grn != row["name"]:
                dbgrn.grn = row["name"]
                changed = True

            if dbgrn.disabled != disabled:
                dbgrn.disabled = disabled
                changed = True

            if changed:
                updated += 1

    # Should not really happen in practice...
    for dbgrn in grns.values():
        session.delete(dbgrn)
        deleted += 1

    if logger:
        logger.client_info("Added %d, updated %d, deleted %d GRNs." %
                           (added, updated, deleted))

    session.flush()
    return
