-- ON DELETE SET NULL was missing
ALTER TABLE a_record DROP CONSTRAINT a_record_reverse_fk;
ALTER TABLE a_record ADD CONSTRAINT a_record_reverse_fk FOREIGN KEY (reverse_ptr_id) REFERENCES fqdn (id) ON DELETE SET NULL;

-- ON DELETE CASCADE was missing
ALTER TABLE operating_system DROP CONSTRAINT os_arch_fk;
ALTER TABLE operating_system ADD CONSTRAINT os_arch_fk FOREIGN KEY (archetype_id) REFERENCES archetype (id) ON DELETE CASCADE;

QUIT;
