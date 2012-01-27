ALTER TABLE resholder DROP CONSTRAINT resholder_bundle_fk;
ALTER TABLE resholder ADD CONSTRAINT resholder_bundle_fk FOREIGN KEY (resourcegroup_id) REFERENCES resourcegroup (id) ON DELETE CASCADE;

COMMIT;
