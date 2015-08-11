- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE feature ADD activation VARCHAR(10);
ALTER TABLE feature ADD deactivation VARCHAR(10);
QUIT;
~

