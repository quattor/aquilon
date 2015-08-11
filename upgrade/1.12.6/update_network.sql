ALTER TABLE network ADD network_compartment_id INTEGER;
ALTER TABLE network
	ADD CONSTRAINT "NETWORK_NETWORK_COMPARTMENT_FK"
	FOREIGN KEY (network_compartment_id)
        REFERENCES network_compartment (id);

QUIT;
