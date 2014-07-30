ALTER TABLE interface ADD new_mac INTEGER;

UPDATE interface SET new_mac = TO_NUMBER(REPLACE(mac, ':'), 'xxxxxxxxxxxx') WHERE mac IS NOT NULL;

ALTER TABLE interface DROP CONSTRAINT iface_mac_addr_uk;
DROP INDEX iface_mac_addr_uk;
ALTER TABLE interface ADD CONSTRAINT iface_mac_addr_uk UNIQUE (new_mac);
ALTER TABLE interface DROP COLUMN mac;
ALTER TABLE interface RENAME COLUMN new_mac TO mac;
ALTER TABLE interface ADD CONSTRAINT interface_mac_ck CHECK (mac >= 0 AND mac < 281474976710656);

ALTER TABLE observed_mac ADD new_mac_address INTEGER;

UPDATE observed_mac SET new_mac_address = TO_NUMBER(REPLACE(mac_address, ':'), 'xxxxxxxxxxxx');

ALTER TABLE observed_mac DROP CONSTRAINT observed_mac_mac_address_nn;
ALTER TABLE observed_mac MODIFY (new_mac_address INTEGER CONSTRAINT observed_mac_mac_address_nn NOT NULL);
ALTER TABLE observed_mac DROP PRIMARY KEY DROP INDEX;
ALTER TABLE observed_mac ADD CONSTRAINT observed_mac_pk PRIMARY KEY (network_device_id, port, new_mac_address);
ALTER TABLE observed_mac DROP COLUMN mac_address;
ALTER TABLE observed_mac RENAME COLUMN new_mac_address TO mac_address;
ALTER TABLE observed_mac ADD CONSTRAINT observed_mac_mac_address_ck CHECK (mac_address >= 0 AND mac_address < 281474976710656);

QUIT;
