#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" intended to add pre-seeded data for the migration """

from depends import *

def upgrade(dbf):
    verari_id = dbf.get_id("vendor", "name", "verari")
    if not verari_id:
        print "Adding verari"
        dbf.safe_execute("INSERT INTO vendor (id, name, creation_date) VALUES (vendor_id_seq.NEXTVAL, :vendor, :now)",
                vendor="verari", now=datetime.now())
        verari_id = dbf.get_id("vendor", "name", "verari")

    hp_id = dbf.get_id("vendor", "name", "hp")
    blade_id = dbf.get_id("machine_type", "type", "blade")

    m1_id = dbf.get_id("model", "name", "bl260c")
    if not m1_id:
        print "Adding bl260c"
        dbf.safe_execute("INSERT INTO model (id, name, vendor_id, machine_type_id, creation_date) VALUES (model_id_seq.NEXTVAL, :model, :vendor_id, :machine_type_id, :now)",
                model="bl260c", vendor_id=hp_id, machine_type_id=blade_id,
                now=datetime.now())
        m1_id = dbf.get_id("model", "name", "bl260c")

    m2_id = dbf.get_id("model", "name", "vb1205xm")
    if not m2_id:
        print "Adding vb1205xm"
        dbf.safe_execute("INSERT INTO model (id, name, vendor_id, machine_type_id, creation_date) VALUES (model_id_seq.NEXTVAL, :model, :vendor_id, :machine_type_id, :now)",
                model="vb1205xm", vendor_id=verari_id, machine_type_id=blade_id,
                now=datetime.now())
        m2_id = dbf.get_id("model", "name", "vb1205xm")

    intel_id = dbf.get_id("vendor", "name", "intel")

    xeon_id = dbf.get_id("cpu", "name", "xeon_2500")
    if not xeon_id:
        print "Adding xeon_2500"
        dbf.safe_execute("INSERT INTO cpu (id, name, vendor_id, speed, creation_date) VALUES (cpu_id_seq.NEXTVAL, :cpu, :vendor_id, :cpu_speed, :now)",
                cpu="xeon_2500", vendor_id=intel_id, cpu_speed=2500,
                now=datetime.now())
        xeon_id = dbf.get_id("cpu", "name", "xeon_2500")

    scsi_id = dbf.get_id("disk_type", "type", "scsi")

    ms1_id = dbf.get_id("machine_specs", "model_id", m1_id)
    if not ms1_id:
        print "Adding specs for bl260c"
        dbf.safe_execute("INSERT INTO machine_specs (id, model_id, cpu_id, cpu_quantity, memory, disk_type_id, disk_capacity, nic_count, creation_date) VALUES (mach_specs_id_seq.NEXTVAL, :model, :cpu_id, :cpu_quantity, :memory, :disk_type_id, :disk_capacity, :nic_count, :now)",
                model=m1_id, cpu_id=xeon_id, cpu_quantity=2, memory=24576,
                disk_type_id=scsi_id, disk_capacity=36, nic_count=2,
                now=datetime.now())
        ms1_id = dbf.get_id("machine_specs", "model_id", m1_id)

    ms2_id = dbf.get_id("machine_specs", "model_id", m2_id)
    if not ms2_id:
        print "Adding specs for vb1205xm"
        dbf.safe_execute("INSERT INTO machine_specs (id, model_id, cpu_id, cpu_quantity, memory, disk_type_id, disk_capacity, nic_count, creation_date) VALUES (mach_specs_id_seq.NEXTVAL, :model, :cpu_id, :cpu_quantity, :memory, :disk_type_id, :disk_capacity, :nic_count, :now)",
                model=m2_id, cpu_id=xeon_id, cpu_quantity=2, memory=24576,
                disk_type_id=scsi_id, disk_capacity=36, nic_count=2,
                now=datetime.now())
        ms2_id = dbf.get_id("machine_specs", "model_id", m2_id)

    bunker_id = dbf.get_id("location_type", "type", "bunker")
    if not bunker_id:
        print "Adding bunker"
        dbf.safe_execute("INSERT INTO location_type (id, type, creation_date) VALUES (location_type_id_seq.NEXTVAL, :location_type, :now)",
                location_type="bunker", now=datetime.now())
        bunker_id = dbf.get_id("location_type", "type", "bunker")

    rack_section_id = dbf.get_id("location_type", "type", "rack_section")
    if not rack_section_id:
        print "Adding rack_section"
        dbf.safe_execute("INSERT INTO location_type (id, type, creation_date) VALUES (location_type_id_seq.NEXTVAL, :location_type, :now)",
                location_type="rack_section", now=datetime.now())
        rack_section_id = dbf.get_id("location_type", "type", "rack_section")

    devin1_id = dbf.get_id("dns_domain", "name", "devin1.ms.com")
    if not devin1_id:
        print "Adding devin1.ms.com"
        dbf.safe_execute("INSERT INTO dns_domain (id, name, creation_date) VALUES (dns_domain_id_seq.NEXTVAL, :dns_domain, :now)",
                dns_domain="devin1.ms.com", now=datetime.now())
        devin1_id = dbf.get_id("dns_domain", "name", "devin1.ms.com")

    theha_id = dbf.get_id("dns_domain", "name", "theha.ms.com")
    if not theha_id:
        print "Adding theha.ms.com"
        dbf.safe_execute("INSERT INTO dns_domain (id, name, creation_date) VALUES (dns_domain_id_seq.NEXTVAL, :dns_domain, :now)",
                dns_domain="theha.ms.com", now=datetime.now())



def downgrade(dbf):
    rack_section_id = dbf.get_id("location_type", "type", "rack_section")
    theha_id = dbf.get_id("dns_domain", "name", "theha.ms.com")
    devin1_id = dbf.get_id("dns_domain", "name", "devin1.ms.com")
    bunker_id = dbf.get_id("location_type", "type", "bunker")
    m1_id = dbf.get_id("model", "name", "bl260c")
    m2_id = dbf.get_id("model", "name", "vb1205xm")
    ms1_id = dbf.get_id("machine_specs", "model_id", m1_id)
    ms2_id = dbf.get_id("machine_specs", "model_id", m2_id)
    xeon_id = dbf.get_id("cpu", "name", "xeon_2500")
    scsi_id = dbf.get_id("disk_type", "type", "scsi")
    intel_id = dbf.get_id("vendor", "name", "intel")
    verari_id = dbf.get_id("vendor", "name", "verari")
    hp_id = dbf.get_id("vendor", "name", "hp")
    blade_id = dbf.get_id("machine_type", "type", "blade")



    dbf.safe_execute("DELETE FROM dns_domain where id = :id", id=devin1_id)
    dbf.safe_execute("DELETE FROM dns_domain where id = :id", id=theha_id)
    dbf.safe_execute("DELETE FROM location_type where id = :id", id=bunker_id)
    dbf.safe_execute("DELETE FROM location_type where id = :id",
            id=rack_section_id)
    dbf.safe_execute("DELETE FROM machine_specs where id = :id", id=ms1_id)
    dbf.safe_execute("DELETE FROM machine_specs where id = :id", id=ms2_id)
    dbf.safe_execute("DELETE FROM cpu where id = :id", id=xeon_id)
    dbf.safe_execute("DELETE FROM model where id = :id", id=m1_id)
    dbf.safe_execute("DELETE FROM model where id = :id", id=m2_id)
    dbf.safe_execute("DELETE FROM vendor where id = :id", id=verari_id)
