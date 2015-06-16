ALTER TABLE application RENAME COLUMN eonid TO eon_id;
ALTER TABLE application RENAME CONSTRAINT application_eonid_nn TO application_eon_id_nn;
ALTER TABLE application ADD CONSTRAINT application_grn_fk FOREIGN KEY (eon_id) REFERENCES grn (eon_id);

QUIT;
