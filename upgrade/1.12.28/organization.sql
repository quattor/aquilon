ALTER TABLE company RENAME TO organization;
ALTER TABLE organization RENAME CONSTRAINT company_id_nn TO organization_id_nn;
ALTER TABLE organization RENAME CONSTRAINT company_location_fk TO organization_location_fk;
ALTER TABLE organization RENAME CONSTRAINT company_pk TO organization_pk;
ALTER INDEX company_pk RENAME TO organization_pk;

UPDATE location SET location_type = 'organization' WHERE location_type = 'company';

QUIT;
