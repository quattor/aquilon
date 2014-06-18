ALTER TABLE domain ADD archived INTEGER;
ALTER TABLE domain ADD CONSTRAINT domain_archived_ck CHECK (archived IN (0, 1));
UPDATE domain SET archived = 0;
ALTER TABLE domain MODIFY (archived INTEGER CONSTRAINT domain_archived_nn NOT NULL);

QUIT;
