ALTER TABLE dns_record ADD owner_eon_id INTEGER;
ALTER TABLE dns_record ADD CONSTRAINT dns_record_owner_grn_fk FOREIGN KEY (owner_eon_id) REFERENCES Grn (eon_id);
