-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

CREATE TABLE asset_lifecycle (
	id INTEGER CONSTRAINT asset_lifecycle_id_nn NOT NULL,
	name VARCHAR2(32) CONSTRAINT asset_lifecycle_name_nn NOT NULL,
	creation_date DATE CONSTRAINT asset_lifecycle_cr_date_nn NOT NULL,
	CONSTRAINT asset_lifecycle_name_uk UNIQUE (name),
	CONSTRAINT asset_lifecycle_pk PRIMARY KEY (id)
);

CREATE SEQUENCE asset_lifecycle_id_seq;

INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'evaluation');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'decommissioned');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'pre_prod');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'early_prod');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'production');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'pre_decommission');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'inactive');
INSERT INTO asset_lifecycle (id, creation_date, name) VALUES (asset_lifecycle_id_seq.NEXTVAL, SYSDATE, 'withdrawn');

ALTER TABLE operating_system ADD lifecycle_id INTEGER;
UPDATE operating_system SET lifecycle_id = (SELECT id FROM asset_lifecycle WHERE name = 'production');
ALTER TABLE operating_system MODIFY (lifecycle_id CONSTRAINT os_lifecycle_id_nn NOT NULL);
ALTER TABLE operating_system ADD CONSTRAINT os_asset_lifecycle_fk FOREIGN KEY (lifecycle_id) REFERENCES asset_lifecycle (id);
QUIT;
