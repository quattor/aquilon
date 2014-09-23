-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE feature ADD owner_eon_id INTEGER;
ALTER TABLE feature ADD visibility VARCHAR(16);
ALTER TABLE feature ADD CONSTRAINT feature_owner_grn_fk FOREIGN KEY (owner_eon_id) REFERENCES grn (eon_id);
UPDATE feature SET owner_eon_id = 6980;
UPDATE feature set visibility = 'public';
ALTER TABLE feature MODIFY (owner_eon_id CONSTRAINT feature_owner_eon_id_nn NOT NULL);
ALTER TABLE feature MODIFY (visibility CONSTRAINT feature_visibility_nn NOT NULL);
QUIT;
