ALTER TABLE build_item DROP PRIMARY KEY DROP INDEX;
ALTER TABLE build_item DROP CONSTRAINT build_item_uk;
DROP INDEX build_item_uk;
ALTER TABLE build_item DROP COLUMN id;
ALTER TABLE build_item DROP COLUMN creation_date;
ALTER TABLE build_item DROP COLUMN comments;
ALTER TABLE build_item ADD CONSTRAINT build_item_pk PRIMARY KEY (host_id, service_instance_id);

QUIT;
