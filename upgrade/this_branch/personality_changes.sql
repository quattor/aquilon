
/* modify personality table for new field and constraint */
ALTER TABLE PERSONALITY add config_override INTEGER default 0;
ALTER TABLE PERSONALITY add CONSTRAINT persona_cfg_override_ck CHECK (config_override IN (0, 1));
COMMIT;
QUIT;
