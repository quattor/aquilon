/* modify personality table for new field and constraint */
ALTER TABLE PERSONALITY ADD config_override NUMBER(*,0);

UPDATE PERSONALITY SET config_override = 0;

ALTER TABLE PERSONALITY add CONSTRAINT persona_cfg_override_ck CHECK (config_override IN (0, 1)) ENABLE;
ALTER TABLE PERSONALITY MODIFY (config_override NUMBER(*,0) CONSTRAINT "CONFIG_OVERRIDE_NN" NOT NULL);
COMMIT;
QUIT;
