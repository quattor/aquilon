ALTER TABLE realm ADD trusted INTEGER;
ALTER TABLE realm ADD CONSTRAINT realm_trusted_ck CHECK (trusted IN (0, 1));
UPDATE realm SET trusted = 1;
ALTER TABLE realm MODIFY (trusted INTEGER CONSTRAINT realm_trusted_nn NOT NULL);

QUIT;
