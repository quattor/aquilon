ALTER TABLE a_record ADD reverse_ptr_id INTEGER;
ALTER TABLE a_record ADD CONSTRAINT a_record_reverse_fk FOREIGN KEY (reverse_ptr_id) REFERENCES fqdn (id);

QUIT;
