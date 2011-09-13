ALTER TABLE machine_specs ADD nic_model_id INTEGER;
ALTER TABLE machine_specs ADD CONSTRAINT "MACH_SPEC_NIC_MODEL_FK" FOREIGN KEY (nic_model_id) REFERENCES model (id);

UPDATE machine_specs SET nic_model_id = (SELECT id FROM model WHERE machine_type = 'nic' AND name = 'generic_nic');

ALTER TABLE machine_specs MODIFY (nic_model_id INTEGER CONSTRAINT "MCHN_SPECS_NIC_MODEL_ID_NN" NOT NULL);

QUIT;
