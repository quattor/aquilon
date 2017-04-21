ALTER TABLE domain ADD auto_compile INTEGER;
UPDATE domain SET auto_compile = 1;
ALTER TABLE domain MODIFY (auto_compile INTEGER CONSTRAINT domain_auto_compile_nn NOT NULL);
ALTER TABLE domain ADD CONSTRAINT domain_auto_compile_ck CHECK (auto_compile IN (0, 1));

QUIT;
