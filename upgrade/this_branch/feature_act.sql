-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE feature ADD activation VARCHAR2(10 CHAR);
ALTER TABLE feature ADD deactivation VARCHAR2(10 CHAR);
QUIT;
