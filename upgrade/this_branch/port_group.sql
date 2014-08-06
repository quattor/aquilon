CREATE TABLE port_group (
	id INTEGER CONSTRAINT port_group_id_nn NOT NULL,
	network_id INTEGER CONSTRAINT port_group_network_id_nn NOT NULL,
	network_tag INTEGER CONSTRAINT port_group_network_tag_nn NOT NULL,
	usage VARCHAR2(32) CONSTRAINT port_group_usage_nn NOT NULL,
	creation_date DATE CONSTRAINT port_group_cr_date_nn NOT NULL,
	CONSTRAINT port_group_network_uk UNIQUE (network_id),
	CONSTRAINT port_group_network_fk FOREIGN KEY (network_id) REFERENCES network (id) ON DELETE CASCADE,
	CONSTRAINT port_group_pk PRIMARY KEY (id)
);

CREATE SEQUENCE port_group_seq;

DECLARE
	CURSOR pg_curs IS
		SELECT ov.network_id, ov.vlan_id, vi.vlan_type, MAX(ov.creation_date) AS creation_date
		FROM observed_vlan ov JOIN vlan_info vi ON ov.vlan_id = vi.vlan_id
		GROUP BY ov.network_id, ov.vlan_id, vi.vlan_type;
	pg_rec pg_curs%ROWTYPE;
BEGIN
	FOR pg_rec IN pg_curs LOOP
		INSERT INTO port_group (id, network_id, network_tag, usage, creation_date)
			VALUES (port_group_seq.NEXTVAL, pg_rec.network_id, pg_rec.vlan_id, pg_rec.vlan_type, pg_rec.creation_date);
	END LOOP;
END;
/

CREATE INDEX port_group_usage_tag_idx ON port_group (usage, network_tag) COMPRESS 1;

ALTER TABLE observed_vlan ADD port_group_id INTEGER;
UPDATE observed_vlan SET port_group_id = (SELECT id FROM port_group WHERE observed_vlan.network_id = port_group.network_id);
ALTER TABLE observed_vlan MODIFY port_group_id INTEGER CONSTRAINT observed_vlan_port_group_id_nn NOT NULL;

ALTER TABLE observed_vlan DROP PRIMARY KEY DROP INDEX;
ALTER TABLE observed_vlan DROP COLUMN network_id;
ALTER TABLE observed_vlan DROP COLUMN vlan_id;
ALTER TABLE observed_vlan DROP COLUMN creation_date;
ALTER TABLE observed_vlan ADD CONSTRAINT observed_vlan_pk PRIMARY KEY (network_device_id, port_group_id);
ALTER TABLE observed_vlan ADD CONSTRAINT obs_vlan_pg_fk FOREIGN KEY (port_group_id) REFERENCES port_group (id) ON DELETE CASCADE;

CREATE INDEX observed_vlan_pg_idx ON observed_vlan (port_group_id);

ALTER TABLE interface RENAME COLUMN port_group TO port_group_name;

ALTER TABLE interface ADD port_group_id INTEGER;
ALTER TABLE interface ADD CONSTRAINT iface_pg_fk FOREIGN KEY (port_group_id) REFERENCES port_group (id);
ALTER TABLE interface ADD CONSTRAINT iface_pg_ck CHECK (port_group_id IS NULL OR port_group_name IS NULL);

DECLARE
	CURSOR vm_iface_curs IS
		SELECT interface.id, port_group.id AS pg_id
		FROM interface JOIN hardware_entity ON interface.hardware_entity_id = hardware_entity.id
			JOIN model ON hardware_entity.model_id = model.id
			JOIN virtual_machine ON virtual_machine.machine_id = hardware_entity.id
			JOIN "resource" ON virtual_machine.resource_id = "resource".id
			JOIN resholder ON "resource".holder_id = resholder.id
			JOIN clstr ON resholder.cluster_id = clstr.id
			JOIN esx_cluster ON esx_cluster.esx_cluster_id = clstr.id
			JOIN network_device ON esx_cluster.network_device_id = network_device.hardware_entity_id
			JOIN observed_vlan ON network_device.hardware_entity_id = observed_vlan.network_device_id
			JOIN port_group ON observed_vlan.port_group_id = port_group.id
			JOIN vlan_info ON port_group.usage = vlan_info.vlan_type AND port_group.network_tag = vlan_info.vlan_id
		WHERE (model.model_type = 'virtual_machine' OR model.model_type = 'virtual_appliance')
			AND vlan_info.port_group = interface.port_group_name
		FOR UPDATE OF interface.port_group_name, interface.port_group_id;
	vm_iface_rec vm_iface_curs%ROWTYPE;
BEGIN
	FOR vm_iface_rec IN vm_iface_curs LOOP
		UPDATE interface SET port_group_name = NULL, port_group_id = vm_iface_rec.pg_id WHERE CURRENT OF vm_iface_curs;
	END LOOP;
END;
/

COMMIT;
QUIT;
