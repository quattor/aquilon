ALTER TABLE domain ADD requires_tcm NUMBER(*, 0);
UPDATE domain SET requires_tcm = 0;
UPDATE domain SET requires_tcm = 1 WHERE name = 'prod';
UPDATE domain SET requires_tcm = 1 WHERE name = 'secure-aquilon-prod';
ALTER TABLE domain ADD CONSTRAINT "DOMAIN_REQUIRES_TCM_CK" CHECK (requires_tcm IN (0, 1)) ENABLE;
ALTER TABLE domain MODIFY (requires_tcm CONSTRAINT "DOMAIN_REQUIRES_TCM_NN" NOT NULL ENABLE);
COMMIT;
