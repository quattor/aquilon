-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE operating_system ADD lifecycle VARCHAR2(20 CHAR);
UPDATE operating_system SET lifecycle = 'production';
ALTER TABLE operating_system MODIFY (lifecycle CONSTRAINT "OS_LIFECYCLE_NN" NOT NULL);
QUIT;
