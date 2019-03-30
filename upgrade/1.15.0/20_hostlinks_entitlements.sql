CREATE TABLE hostlink_entitlement_map (
	resource_id INTEGER NOT NULL,
	entitlement_id INTEGER NOT NULL,
	CONSTRAINT hostlink_entitlement_map_pk PRIMARY KEY (resource_id, entitlement_id),
	CONSTRAINT hl_entit_map_resource_fk FOREIGN KEY(resource_id) REFERENCES "resource" (id) ON DELETE CASCADE,
	CONSTRAINT hl_entit_map_entitlement_fk FOREIGN KEY(entitlement_id) REFERENCES entitlement (id) ON DELETE CASCADE
);
