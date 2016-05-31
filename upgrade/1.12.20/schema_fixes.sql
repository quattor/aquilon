ALTER TABLE user_principal DROP CONSTRAINT user_principal_name_realm_uk;
DROP INDEX user_principal_name_realm_uk;
ALTER TABLE user_principal ADD CONSTRAINT user_principal_realm_name_uk UNIQUE (realm_id, name);
ALTER INDEX user_principal_realm_name_uk REBUILD COMPRESS;

QUIT;

