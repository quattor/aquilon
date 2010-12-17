-- Convert address_assignment to reference interface directly
ALTER TABLE address_assignment ADD interface_id INTEGER;
UPDATE address_assignment SET interface_id = (SELECT interface_id
						FROM vlan_interface
						WHERE vlan_interface.id = address_assignment.vlan_interface_id);
ALTER TABLE address_assignment DROP CONSTRAINT "ADDR_ASSIGN_VLAN_IP_UK";
ALTER TABLE address_assignment DROP CONSTRAINT "ADDR_ASSIGN_VLAN_LABEL_UK";
ALTER TABLE address_assignment DROP CONSTRAINT "ADDR_ASSIGN_VLAN_ID_FK";
ALTER TABLE address_assignment DROP COLUMN vlan_interface_id;
ALTER TABLE address_assignment
	MODIFY (interface_id CONSTRAINT "ADDR_ASSIGN_INTERFACE_ID_NN" NOT NULL);
ALTER TABLE address_assignment
	ADD CONSTRAINT "ADDR_ASSIGN_IFACE_LABEL_UK" UNIQUE (interface_id, label);
ALTER TABLE address_assignment
	ADD CONSTRAINT "ADDR_ASSIGN_IFACE_IP_UK" UNIQUE (interface_id, ip);
ALTER TABLE address_assignment
	ADD CONSTRAINT "ADDR_ASSIGN_INTERFACE_ID_FK" FOREIGN KEY (interface_id) REFERENCES interface (id) ON DELETE CASCADE;

-- Drop vlan_interface
DROP TABLE vlan_interface;

-- New interface columns for VLANs
ALTER TABLE interface ADD parent_id INTEGER;
ALTER TABLE interface ADD vlan_id INTEGER;
ALTER TABLE interface
	ADD CONSTRAINT "IFACE_VLAN_CK" CHECK ((parent_id IS NOT NULL AND vlan_id > 0 AND vlan_id < 4096) OR interface_type <> 'vlan');
ALTER TABLE interface
	ADD CONSTRAINT "IFACE_PARENT_VLAN_UK" UNIQUE (parent_id, vlan_id);
ALTER TABLE interface
	ADD CONSTRAINT "IFACE_VLAN_PARENT_FK" FOREIGN KEY (parent_id) REFERENCES interface (id) ON DELETE CASCADE;

QUIT;
