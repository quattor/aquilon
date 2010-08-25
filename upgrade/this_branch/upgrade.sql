-- In case of an error, we want to know which command have failed
set echo on;

-- Drop system.mac
ALTER TABLE system DROP CONSTRAINT "SYSTEM_PT_UK";
ALTER TABLE system DROP COLUMN mac;
ALTER TABLE system ADD CONSTRAINT "SYSTEM_PT_UK" UNIQUE (name, dns_domain_id, ip);

QUIT;
