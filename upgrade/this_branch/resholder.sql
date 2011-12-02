ALTER TABLE resholder ADD resourcegroup_id INTEGER;
ALTER TABLE resholder ADD CONSTRAINT resholder_bundle_fk 
      FOREIGN KEY(resourcegroup_id) REFERENCES resourcegroup (id) 
      ON DELETE CASCADE;
COMMIT;
