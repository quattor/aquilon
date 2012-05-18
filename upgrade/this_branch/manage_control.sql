ALTER TABLE domain ADD allow_manage INTEGER DEFAULT 1;
ALTER TABLE domain ADD CONSTRAINT domain_allow_manage_ck CHECK (allow_manage IN (0, 1));
UPDATE domain SET allow_manage = 1;
ALTER TABLE domain MODIFY (allow_manage INTEGER CONSTRAINT domain_allow_manage_nn NOT NULL);

COMMIT;
QUIT;
