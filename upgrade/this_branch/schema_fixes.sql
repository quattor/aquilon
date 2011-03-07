-- The index exists, but the constraint does not
ALTER TABLE hardware_entity
	ADD CONSTRAINT "HARDWARE_ENTITY_LABEL_UK" UNIQUE (label);

-- Columns in the DB are smaller than in the model
ALTER TABLE machine_specs MODIFY disk_type VARCHAR2(64);
ALTER TABLE machine_specs MODIFY controller_type VARCHAR2(64);

-- Wrong constraint name
ALTER TABLE host
	RENAME CONSTRAINT "HOST_STATUS_ID_NN" TO "HOST_LIFECYCLE_ID_NN";

-- Missing ON DELETE CASCADE
ALTER TABLE personality_service_map
	DROP CONSTRAINT "PRSNLTY_SVC_MAP_SVC_INST_FK";
ALTER TABLE personality_service_map
	ADD CONSTRAINT "PRSNLTY_SVC_MAP_SVC_INST_FK"
		FOREIGN KEY (service_instance_id)
		REFERENCES service_instance (id)
		ON DELETE CASCADE;

-- Extra ON DELETE CASCADE
ALTER TABLE router_address
	DROP CONSTRAINT "ROUTER_ADDRESS_NETWORK_FK";
ALTER TABLE router_address
	ADD CONSTRAINT "ROUTER_ADDRESS_NETWORK_FK"
		FOREIGN KEY (network_id)
		REFERENCES network (id);

-- Missing ON DELETE CASCADE
ALTER TABLE service_map
	DROP CONSTRAINT "SVC_MAP_SVC_INST_FK";
ALTER TABLE service_map
	ADD CONSTRAINT "SVC_MAP_SVC_INST_FK"
		FOREIGN KEY (service_instance_id)
		REFERENCES service_instance (id)
		ON DELETE CASCADE;

-- UNIQUE constraint was dropped, index was not
DROP INDEX "NETWORK_IP_UK";

QUIT;
