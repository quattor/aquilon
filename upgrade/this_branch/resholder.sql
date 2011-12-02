ALTER TABLE resholder ADD resourcegroup_id INTEGER;
ALTER TABLE resholder ADD CONSTRAINT resholder_bundle_fk 
      FOREIGN KEY(resourcegroup_id) REFERENCES "resource" (id)
      ON DELETE CASCADE;
COMMIT;
