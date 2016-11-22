ALTER TABLE service ADD allow_alias_bindings INTEGER;
ALTER TABLE service ADD CONSTRAINT service_allow_alias_bindings_ck CHECK (allow_alias_bindings IN (0, 1));
UPDATE service SET allow_alias_bindings = 0;
ALTER TABLE service MODIFY (allow_alias_bindings INTEGER CONSTRAINT service_allow_alias_bindings_nn NOT NULL);

QUIT;
