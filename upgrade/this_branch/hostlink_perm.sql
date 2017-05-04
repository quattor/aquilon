ALTER TABLE hostlink ADD mode INTEGER DEFAULT NULL;
ALTER TABLE hostlink ADD CONSTRAINT hostlink_mode_id_ok CHECK (mode > 0 AND mode <= 1023);
