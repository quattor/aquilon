- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE param_definition ADD activation VARCHAR(10);
ALTER TABLE param_definition DROP rebuild_required;
QUIT;
~

