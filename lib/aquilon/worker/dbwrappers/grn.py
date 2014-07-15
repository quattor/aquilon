# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

import cdb

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Grn
from aquilon.worker.locks import SyncKey


def lookup_by_name(config, grn):
    name = os.path.join(config.get("broker", "grn_to_eonid_map_location"),
                        "eon_catalog_by_name.cdb")
    cdb_file = cdb.init(name)
    # cdb_file is not iterable, so tell pep8 not to warn about .has_key()
    return cdb_file.has_key(grn)  # noqa


def lookup_by_id(config, eon_id):
    name = os.path.join(config.get("broker", "grn_to_eonid_map_location"),
                        "eon_catalog_by_id.cdb")
    cdb_file = cdb.init(name)
    # cdb_file is not iterable, so tell pep8 not to warn about .has_key()
    return cdb_file.has_key(str(eon_id))  # noqa


def lookup_autoupdate(config, session, logger, grn, eon_id):
    # Check the CDB file first, since that quickly tells us if the cache is
    # stale or if just the input is wrong
    if grn and not lookup_by_name(config, grn):
        return None
    elif eon_id and not lookup_by_id(config, eon_id):
        return None

    with SyncKey(data="grn", logger=logger):
        # Try again in case a concurrent process have already updated the cache
        # by the time we got the lock
        dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
        if dbgrn:  # pragma: no cover
            return dbgrn

        update_grn_map(config, session, logger)
        dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
    return dbgrn


def lookup_grn(session, grn=None, eon_id=None, usable_only=True, logger=None,
               config=None, autoupdate=True):
    dbgrn = Grn.get_unique(session, grn=grn, eon_id=eon_id)
    if not dbgrn and autoupdate:
        if not config or not config.get("broker", "grn_to_eonid_map_location"):  # pragma: no cover
            return None
        dbgrn = lookup_autoupdate(config, session, logger, grn, eon_id)

    if not dbgrn:
        if grn:
            raise NotFoundException("GRN %s not found." % grn)
        else:
            raise NotFoundException("EON ID %s not found." % eon_id)

    if usable_only and dbgrn.disabled:
        raise ArgumentError("GRN %s is not usable for new systems." % dbgrn.grn)

    return dbgrn


def update_grn_map(config, session, logger):
    if not config.get("broker", "grn_to_eonid_map_location"):  # pragma: no cover
        raise ArgumentError("GRN synchronization is disabled.")

    q = session.query(Grn)
    grns = {}
    for dbgrn in q:
        grns[dbgrn.eon_id] = dbgrn

    name = os.path.join(config.get("broker", "grn_to_eonid_map_location"),
                        "eon_catalog.csv")
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
