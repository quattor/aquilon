CREATE TABLE machines (
               ether varchar(17) primary key,
               machine varchar(255),
               hostname varchar(255),
               aqhostname varchar(255),
               windowshostname varchar(255),
               sysloc varchar(64),
               hwvendor varchar(32),
               hwmodel varchar(64)
            );

-- Hosts without a windowshostname should be ignored.
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("02:02:04:02:01:05", "ut3c1n3", "unittest00.one-nyp.ms.com", "unittest00.one-nyp.ms.com", NULL, "ut.ny.na", "ibm", "hs21-885315u");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("02:02:04:02:01:02", "ut3c5n10", "unittest02.one-nyp.ms.com", "unittest02.one-nyp.ms.com", NULL, "ut.ny.na", "ibm", "hs21-885315u");
-- Missing DNS Domain
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:00", "evm1", "badhost1", NULL, "badhost1", "ut.ny.na", "utvendor", "utmedium");
-- Invalid DNS Domain
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:01", "evm2", "badhost2.domain-does-not-exist.ms.com", NULL, "badhost2.domain-does-not-exist.ms.com", "ut.ny.na", "utvendor", "utmedium");
-- MAC address that does not exist in AQDB
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("02:00:00:00:00:00", "badmachine", "badhost3.msad.ms.com", NULL, "badhost3.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
-- Valid hostname where the mac is already taken by a chassis.
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("02:02:04:02:01:08", "ut3c5", "ut3c5.aqd-unittest.ms.com", "badhost4.msad.ms.com", "badhost4.msad.ms.com", "ut.ny.na", "aurora_vendor", "utchassis");
-- Valid Windows hostname that is not covered by refresh
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("02:02:04:02:01:07", "ut3c1n4", "unittest01.one-nyp.ms.com", "badhost5.msad.ms.com", "badhost5.msad.ms.com", "ut.ny.na", "ibm", "hs21-885315u");
-- Valid entries
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:02", "evm3", "desktop1.msad.ms.com", NULL, "desktop1.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:03", "evm4", "desktop2.msad.ms.com", NULL, "desktop2.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:04", "evm5", "desktop3.msad.ms.com", NULL, "desktop3.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:05", "evm6", "desktop4.msad.ms.com", NULL, "desktop4.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");

