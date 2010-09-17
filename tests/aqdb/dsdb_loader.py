#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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

import os
import sys
import logging
import math
from shlex import shlex
from inspect import isclass

import utils
utils.load_classpath()

from ipaddr import IPv4Network

import argparse
import ms.modulecmd

from aquilon.config import Config
config = Config()

if config.has_option("database", "module"):
    ms.modulecmd.load(config.get("database", "module"))

from aquilon.exceptions_ import ArgumentError, NotFoundException
from sqlalchemy.exc import IntegrityError
import aquilon.aqdb.model as model
import aquilon.aqdb.dsdb as dsdb_
from aquilon.aqdb.db_factory import DbFactory

def populate_building(session, dsdb, logger):
    missed = 0
    imported = 0
    for building_code, address, city_code in dsdb.dump('building'):
        city = model.City.get_unique(session, name=city_code)
        if not city:
            missed += 1
            continue
        building = model.Building.get_unique(session, name=building_code)
        if building:
            missed += 1
            continue
        building = model.Building(name=building_code, fullname=address, parent=city)
        session.add(building)
        imported += 1
    try:
        session.commit()
    except Exception, err:
        logger.error(err)
        session.rollback()

    logger.debug("Imported %d buildings, skipped %d" % (imported, missed))

def populate_city(session, dsdb, logger):
    missed = 0
    imported = 0
    for city_code, city_name, country_code in dsdb.dump('city'):
        country = model.Country.get_unique(session, name=country_code)
        if not country:
            missed += 1
            continue
        city = model.City.get_unique(session, name=city_code)
        if city:
            missed += 1
            continue
        city = model.City(name=city_code, fullname=city_name, parent=country)
        session.add(city)
        imported += 1
    try:
        session.commit()
    except Exception, err:
        logger.error(err)
        session.rollback()

    logger.debug("Imported %d cities, skipped %d" % (imported, missed))

def populate_country(session, dsdb, logger):
    missed = 0
    imported = 0
    for country_code, country_name, continent_code in dsdb.dump('country'):
        continent = model.Continent.get_unique(session, name=continent_code)
        if not continent:
            missed += 1
            continue
        country = model.Country.get_unique(session, name=country_code)
        if country:
            missed += 1
            continue
        country = model.Country(name=country_code, fullname=country_name,
                                parent=continent)
        session.add(country)
        imported += 1
    try:
        session.commit()
    except Exception, err:
        logger.error(err)
        session.rollback()

    logger.debug("Imported %d countries, skipped %d" % (imported, missed))

def populate_network(session, dsdb, logger, view):
    networks_by_name = {}
    networks_by_ip = {}
    for network in session.query(model.Network):
        networks_by_name[network.name] = 1
        networks_by_ip[network.network] = 1
    session.expire_all()

    missed = 0
    imported = 0
    buildings = {}
    for (net_name, ip_addr, mask, network_type, building_code,
         side) in dsdb.dump(view):

        if imported + missed > 0 and (imported + missed) % 5000 == 0:
            logger.debug("Looked at %d networks..." % (imported + missed))

        netmask = 32 - int(math.log(mask, 2))
        network_addr = IPv4Network("%s/%s" % (ip_addr, netmask))

        if not building_code:
            logger.warning("Network %s has no building" % network_addr)
            missed += 1
            continue

        if building_code in buildings:
            building = buildings[building_code]
        else:
            building = model.Building.get_unique(session, name=building_code)
            if not building:
                missed += 1
                continue
            buildings[building_code] = building

        if net_name in networks_by_name or network_addr in networks_by_ip:
            missed += 1
            continue

        if network_type == 'tor_net' or network_type == 'grid_access':
            is_discoverable = True
        else:
            is_discoverable = False

        network = model.Network(name=net_name, network=network_addr,
                                network_type=network_type, location=building,
                                is_discoverable=is_discoverable, side=side)
        session.add(network)
        imported += 1
        if imported % 3000 == 0:
            try:
                session.commit()
            except Exception, err:
                log.error(err)
                session.rollback()
                break

    try:
        session.commit()
    except Exception, err:
        log.error(err)
        session.rollback()

    logger.debug("Imported %d networks, skipped %d" % (imported, missed))

if __name__ == '__main__':
    logging.basicConfig(levl=logging.ERROR)

    parser = argparse.ArgumentParser(description="Imports data from DSDB to AQDB")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose mode; show objects added")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug mode; show SQL queries")
    parser.add_argument('-f', '--full', action='store_true',
                        help='Perform full network table population',
                        default = False)
    opts = parser.parse_args()

    if opts.debug:
        log = logging.getLogger('sqlalchemy.engine')
        log.setLevel(logging.INFO)

    db = DbFactory(verbose=opts.verbose)
    model.Base.metadata.bind = db.engine
    session = db.Session()

    dsdb = dsdb_.DsdbConnection()

    log = logging.getLogger('aqdb.dsdb_loader')
    if opts.verbose:
        log.setLevel(logging.DEBUG)

    populate_country(session, dsdb, log)
    populate_city(session, dsdb, log)
    populate_building(session, dsdb, log)

    if opts.full:
        populate_network(session, dsdb, log, 'network_full')
    else:
        populate_network(session, dsdb, log, 'np_network')
