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
-- Valid entries.  The first are the same as in badmachines.  The next one
-- repurposes one of the virtual machines from badmachines with a new name.
-- The last is brand new.
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:02", "evm3", "desktop1.msad.ms.com", NULL, "desktop1.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:03", "evm4", "desktop2.msad.ms.com", NULL, "desktop2.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:05", "evm6", "desktop5.msad.ms.com", NULL, "desktop5.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");
INSERT INTO machines (ether, machine, hostname, aqhostname, windowshostname, sysloc, hwvendor, hwmodel) VALUES ("00:50:56:01:20:06", "evm7", "desktop6.msad.ms.com", NULL, "desktop6.msad.ms.com", "ut.ny.na", "utvendor", "utmedium");

