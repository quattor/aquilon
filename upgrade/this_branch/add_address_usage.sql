ALTER TABLE address_assignment
	ADD usage VARCHAR2(16 CHAR);
UPDATE address_assignment SET usage = 'system';	
ALTER TABLE address_assignment
	MODIFY (usage CONSTRAINT "ADDR_ASSIGN_USAGE_NN" NOT NULL);

QUIT;
