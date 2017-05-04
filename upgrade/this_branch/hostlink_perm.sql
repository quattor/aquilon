ALTER TABLE hostlink ADD target_mode INTEGER;
ALTER TABLE hostlink ADD CONSTRAINT hostlink_target_mode_ok CHECK (target_mode > 0 AND target_mode <= 1023);
