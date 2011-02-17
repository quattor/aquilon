ALTER TABLE domain ADD change_manager VARCHAR2(16 CHAR);
UPDATE domain SET change_manager = 'tcm' WHERE domain_id = (SELECT id FROM branch WHERE name = 'prod');
UPDATE domain SET change_manager = 'tcm' WHERE domain_id = (SELECT id FROM branch WHERE name = 'secure-aquilon-prod');
COMMIT;
