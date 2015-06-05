ALTER TABLE cpu DROP CONSTRAINT cpu_vendor_name_speed_uk;
ALTER TABLE cpu DROP COLUMN speed;
ALTER TABLE cpu ADD CONSTRAINT cpu_vendor_name_uk UNIQUE (vendor_id, name);

QUIT;
