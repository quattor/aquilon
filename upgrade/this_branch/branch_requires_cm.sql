ALTER TABLE domain ADD requires_change_manager NUMBER(*,0);
UPDATE domain SET requires_change_manager = 0;
UPDATE domain SET requires_change_manager = 1 WHERE change_manager IS NOT NULL;
ALTER TABLE domain MODIFY
	(requires_change_manager CONSTRAINT "DOMAIN_REQ_CHG_MGR_NN" NOT NULL);
ALTER TABLE domain
        ADD CONSTRAINT "DOMAIN_REQ_CHG_MGR_CK"
        CHECK (requires_change_manager IN (0, 1)) ENABLE;
ALTER TABLE domain DROP COLUMN change_manager;

QUIT;

