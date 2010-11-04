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

"""
Inspect the database and add missing objects that would have been created by the
new commands
"""

import os, sys
import ms.version

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.6")

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

import aquilon.aqdb.depends
import ms.modulecmd

from sqlalchemy.orm import contains_eager, subqueryload_all
from sqlalchemy.sql import exists

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Base, HardwareEntity, Interface, VlanInterface,
                                PrimaryNameAssociation, System, DnsDomain,
                                AddressAssignment)

def add_interfaces(session):
    """ Add a default interface for all HW that has an IP """
    q = session.query(HardwareEntity)
    q = q.filter(~exists().where(Interface.hardware_entity_id == HardwareEntity.id))
    q = q.outerjoin(PrimaryNameAssociation, System, DnsDomain)
    q = q.options(contains_eager('_primary_name_asc'))
    q = q.options(contains_eager('_primary_name_asc.dns_record'))
    q = q.options(contains_eager('_primary_name_asc.dns_record.dns_domain'))
    q = q.filter(System.ip != None)

    hws = q.all()
    count = 0
    for hw in hws:
        if hw.hardware_type == "machine":
            interface = "eth0"
            itype = "public"
        elif hw.hardware_type == "switch":
            interface = "xge"
            itype = "oa"
        else:
            interface = "oa"
            itype = "oa"

        #print "Adding default interface for {0:l}".format(hw)

        dbinterface = Interface(hardware_entity=hw, name=interface,
                                interface_type=itype,
                                comments="Created automatically by upgrade script")
        session.add(dbinterface)
        count += 1

    session.flush()
    print "Added %d interfaces" % count

def add_addresses(session):
    """ Add an AddressAssignment record for every PrimaryNameAssociation """
    q = session.query(PrimaryNameAssociation)
    q = q.join(System, DnsDomain)
    q = q.filter(System.ip != None)
    q = q.filter(~exists().where(AddressAssignment.ip == System.ip))
    q = q.options(contains_eager('dns_record'))
    q = q.options(contains_eager('dns_record.dns_domain'))
    q = q.options(subqueryload_all('hardware_entity.interfaces.vlans.assignments'))
    q = q.options(subqueryload_all('hardware_entity.interfaces._vlan_ids'))

    count = 0
    pnas = q.all()
    for pna in pnas:
        hw = pna.hardware_entity
        if len(hw.interfaces) != 1:
            print "{0} has an unexpected number of interfaces, skipping: " \
                    "{1}".format(hw, len(hw.interfaces))
            continue
        iface = hw.interfaces[0]
        if len(iface.vlans[0].addresses):
            print "{0} already has addresses, skipping".format(iface)
            continue
        #print "Adding AddressAssignment record for {0:l}".format(hw)
        iface.vlans[0].addresses.append(pna.dns_record.ip)
        count += 1

    session.flush()
    print "Added %d AddressAssignment records" % count

def main():
    from aquilon.config import Config

    config = Config()
    if config.has_option("database", "module"):
        ms.modulecmd.load(config.get("database", "module"))

    db = DbFactory()
    Base.metadata.bind = db.engine

    session = db.Session()

    add_interfaces(session)
    add_addresses(session)

    session.rollback()
    raise Exception("Replace the rollback() in the code with commit() when "
                    "ready to go, and disable this exception")
    #session.commit()

if __name__ == '__main__':
    main()
