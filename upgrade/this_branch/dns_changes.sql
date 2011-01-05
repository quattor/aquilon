-- Move ip and network_id from system to future_a_record
ALTER TABLE system DROP CONSTRAINT "SYSTEM_PT_UK";
ALTER TABLE future_a_record ADD ip INTEGER;
ALTER TABLE future_a_record ADD network_id INTEGER;
UPDATE future_a_record SET ip = (SELECT ip FROM system WHERE system.id = future_a_record.system_id);
UPDATE future_a_record SET network_id = (SELECT network_id FROM system WHERE system.id = future_a_record.system_id);
ALTER TABLE future_a_record
	MODIFY (ip CONSTRAINT "FUTURE_A_RECORD_IP_NN" NOT NULL);
ALTER TABLE future_a_record
	ADD CONSTRAINT "FUTURE_A_RECORD_IP_UK" UNIQUE (ip);
ALTER TABLE future_a_record
	ADD CONSTRAINT "FUTURE_A_RECORD_NETWORK_FK"
		FOREIGN KEY (network_id)
		REFERENCES network (id)
		ON DELETE SET NULL;
ALTER TABLE system DROP COLUMN ip;
ALTER TABLE system DROP COLUMN network_id;

QUIT;
