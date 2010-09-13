-- In case of an error, we want to know which command have failed
set echo on;

-- Drop system.mac
ALTER TABLE system DROP CONSTRAINT "SYSTEM_PT_UK";
ALTER TABLE system DROP COLUMN mac;
ALTER TABLE system ADD CONSTRAINT "SYSTEM_PT_UK" UNIQUE (name, dns_domain_id, ip);

-- Add the new fields to hardware_entity
ALTER TABLE hardware_entity ADD label VARCHAR(63);
ALTER TABLE hardware_entity ADD hardware_type VARCHAR(64);

-- Populate hardware_entity.label
UPDATE hardware_entity
	SET label = (SELECT name FROM machine WHERE machine.machine_id = hardware_entity.id)
	WHERE hardware_entity_type = 'machine';
UPDATE hardware_entity
	SET label = (SELECT system.name
			FROM chassis, system
			WHERE chassis.chassis_hw_id = hardware_entity.id AND
				chassis.system_id = system.id)
	WHERE hardware_entity_type = 'chassis_hw';
UPDATE hardware_entity
	SET label = (SELECT system.name
			FROM switch, system
			WHERE switch.switch_id = hardware_entity.id AND
				switch.id = system.id)
	WHERE hardware_entity_type = 'switch_hw';

ALTER TABLE hardware_entity
	MODIFY (label CONSTRAINT "HW_ENT_LABEL_NN" NOT NULL);
-- FIXME
-- SELECT label, hardware_entity_type FROM hardware_entity WHERE label in (SELECT label FROM hardware_entity GROUP BY label HAVING count(*) > 1);
-- Chassis names are apparently not unique:
-- dd950c3 ha476c2 np3c1 dd950c2 dd950c1 ds950c3 oy561c1 ds951c2 ds950c2 ds950c1
-- Full names:
-- dd950c3.ms.com dd950c3.devin1.ms.com ha476c2.ms.com ha476c2.one-nyp.ms.com ha476c2.the-ha.ms.com np3c1.ms.com np3c1.one-nyp.ms.com dd950c2.ms.com dd950c2.devin1.ms.com dd950c1.ms.com dd950c1.devin1.ms.com ds950c3.ms.com ds950c3.devin2.ms.com oy561c1.ms.com oy561c1.heathrow.ms.com ds951c2.ms.com ds951c2.devin2.ms.com ds950c2.ms.com ds950c2.devin2.ms.com ds950c1.ms.com ds950c1.devin2.ms.com
CREATE UNIQUE INDEX "HARDWARE_ENTITY_LABEL_UK" ON hardware_entity(label);

-- Populate hardware_type
UPDATE hardware_entity SET hardware_type = 'machine' WHERE hardware_entity_type = 'machine';
UPDATE hardware_entity SET hardware_type = 'chassis' WHERE hardware_entity_type = 'chassis_hw';
UPDATE hardware_entity SET hardware_type = 'switch' WHERE hardware_entity_type = 'switch_hw';

-- Drop hardware_entity_type and enable non-null check on hardware_type
ALTER TABLE hardware_entity
	DROP COLUMN hardware_entity_type;
ALTER TABLE hardware_entity
	MODIFY (hardware_type CONSTRAINT "HW_ENT_HARDWARE_TYPE_NN" NOT NULL);

-- Drop machine.name
ALTER TABLE machine DROP COLUMN name;

--
-- Make DynamicStub a child of FutureARecord
--
INSERT INTO future_a_record (system_id)
	SELECT system_id FROM dynamic_stub;
ALTER TABLE dynamic_stub DROP CONSTRAINT "DYNAMIC_STUB_SYSTEM_FK";
ALTER TABLE dynamic_stub
	ADD CONSTRAINT "DYNAMIC_STUB_FARECORD_FK" FOREIGN KEY (system_id) REFERENCES future_a_record (system_id) ON DELETE CASCADE;

--
-- Create reserved_name
--
CREATE TABLE reserved_name (
	system_id INTEGER CONSTRAINT "RESERVED_NAME_SYSTEM_ID_NN" NOT NULL,
	CONSTRAINT "RESERVED_NAME_SYSTEM_FK" FOREIGN KEY (system_id) REFERENCES system (id) ON DELETE CASCADE,
	CONSTRAINT "RESERVED_NAME_PK" PRIMARY KEY (system_id)
);

-- Convert old system subclasses to future_a_record/reserved_name
INSERT INTO future_a_record (system_id)
	SELECT id FROM system
		WHERE ip IS NOT NULL AND
			system_type != 'future_a_record' AND
			system_type != 'dynamic_stub';
UPDATE SYSTEM
	SET system_type = 'future_a_record'
	WHERE ip IS NOT NULL AND
		system_type != 'future_a_record' AND
		system_type != 'dynamic_stub';

INSERT INTO reserved_name (system_id)
	SELECT id FROM system
		WHERE ip IS NULL AND system_type != 'reserved_name';
UPDATE system
	SET system_type = 'reserved_name'
	WHERE ip IS NULL AND system_type != 'reserved_name';

--
-- Create primary_name_association
--
CREATE TABLE primary_name_association (
	hardware_entity_id INTEGER CONSTRAINT "PRI_NAME_ASC_HW_ENT_ID_NN" NOT NULL,
	dns_record_id INTEGER CONSTRAINT "PRI_NAME_ASC_DNS_RECORD_ID_NN" NOT NULL,
	creation_date DATE CONSTRAINT "PRI_NAME_ASC_CR_DATE_NN" NOT NULL,
	comments VARCHAR(255),
	CONSTRAINT "PRIMARY_NAME_ASSOCIATION_PK" PRIMARY KEY (hardware_entity_id, dns_record_id),
	CONSTRAINT "PRIMARY_NAME_ASC_HW_ENT_UK" UNIQUE (hardware_entity_id),
	CONSTRAINT "PRIMARY_NAME_ASC_DNS_UK" UNIQUE (dns_record_id),
	CONSTRAINT "PRIMARY_NAME_ASC_HW_FK" FOREIGN KEY (hardware_entity_id) REFERENCES hardware_entity (id),
	CONSTRAINT "PRIMARY_NAME_ASC_DNS_REC_FK" FOREIGN KEY (dns_record_id) REFERENCES system (id) ON DELETE CASCADE
);

--
-- Convert chassis & switch from being based on system to hardware_entity
--

-- Convert chassis_slot to reference chassis_hw instead of chassis
ALTER TABLE chassis_slot DROP CONSTRAINT "CHASSIS_SLOT_CHASSIS_FK";
ALTER TABLE chassis_slot DROP CONSTRAINT "CHASSIS_SLOT_PK";
ALTER TABLE chassis_slot DROP CONSTRAINT "CHASSIS_SLOT_CHASSIS_ID_NN";
ALTER TABLE chassis_slot RENAME COLUMN chassis_id TO chassis_system_id;
ALTER TABLE chassis_slot ADD chassis_id INTEGER;
UPDATE chassis_slot SET chassis_id = (SELECT chassis.chassis_hw_id
						FROM chassis
						WHERE chassis.system_id = chassis_slot.chassis_system_id);
ALTER TABLE chassis_slot
	MODIFY (chassis_id CONSTRAINT "CHASSIS_SLOT_CHASSIS_ID_NN" NOT NULL);
ALTER TABLE chassis_slot
	ADD CONSTRAINT "CHASSIS_SLOT_CHASSIS_FK" FOREIGN KEY (chassis_id) REFERENCES chassis_hw (hardware_entity_id) ON DELETE CASCADE;
ALTER TABLE chassis_slot DROP COLUMN chassis_system_id;
ALTER TABLE chassis_slot
	ADD CONSTRAINT "CHASSIS_SLOT_PK" PRIMARY KEY (chassis_id, slot_number);

-- Convert esx_cluster to reference switch_hw instead of switch
ALTER TABLE esx_cluster DROP CONSTRAINT "ESX_CLUSTER_SWITCH_FK";
ALTER TABLE esx_cluster RENAME COLUMN switch_id TO switch_system_id;
ALTER TABLE esx_cluster ADD switch_id INTEGER;
UPDATE esx_cluster SET switch_id = (SELECT switch.switch_id
						FROM switch
						WHERE switch.id = esx_cluster.switch_system_id);
ALTER TABLE esx_cluster
	ADD CONSTRAINT "ESX_CLUSTER_SWITCH_FK" FOREIGN KEY (switch_id) REFERENCES switch_hw (hardware_entity_id);
ALTER TABLE esx_cluster DROP COLUMN switch_system_id;

-- Convert observed_mac to reference switch_hw instead of switch
ALTER TABLE observed_mac DROP CONSTRAINT "OBS_MAC_HW_FK";
ALTER TABLE observed_mac DROP CONSTRAINT "OBSERVED_MAC_SWITCH_ID_NN";
ALTER TABLE observed_mac DROP CONSTRAINT "OBSERVED_MAC_PK";
ALTER TABLE observed_mac RENAME COLUMN switch_id TO switch_system_id;
ALTER TABLE observed_mac ADD switch_id INTEGER;
UPDATE observed_mac SET switch_id = (SELECT switch.switch_id
						FROM switch
						WHERE switch.id = observed_mac.switch_system_id);
ALTER TABLE observed_mac
	ADD CONSTRAINT "OBS_MAC_HW_FK" FOREIGN KEY (switch_id) REFERENCES switch_hw (hardware_entity_id) ON DELETE CASCADE;
ALTER TABLE observed_mac
	MODIFY (switch_id CONSTRAINT "OBSERVED_MAC_SWITCH_ID_NN" NOT NULL);
ALTER TABLE observed_mac DROP COLUMN switch_system_id;
ALTER TABLE observed_mac
	ADD CONSTRAINT "OBSERVED_MAC_PK" PRIMARY KEY (switch_id, port_number, mac_address, slot);

-- Convert observed_vlan to reference switch_hw instead of switch
ALTER TABLE observed_vlan DROP CONSTRAINT "OBS_VLAN_HW_FK";
ALTER TABLE observed_vlan DROP CONSTRAINT "OBSERVED_VLAN_SWITCH_ID_NN";
ALTER TABLE observed_vlan DROP CONSTRAINT "OBSERVED_VLAN_PK";
ALTER TABLE observed_vlan RENAME COLUMN switch_id TO switch_system_id;
ALTER TABLE observed_vlan ADD switch_id INTEGER;
UPDATE observed_vlan set switch_id = (SELECT switch.switch_id FROM switch
					WHERE switch.id = observed_vlan.switch_system_id);
ALTER TABLE observed_vlan
	ADD CONSTRAINT "OBS_VLAN_HW_FK" FOREIGN KEY (switch_id) REFERENCES switch_hw (hardware_entity_id) ON DELETE CASCADE;
ALTER TABLE observed_vlan
	MODIFY (switch_id CONSTRAINT "OBSERVED_VLAN_SWITCH_ID_NN" NOT NULL);
ALTER TABLE observed_vlan DROP COLUMN switch_system_id;
ALTER TABLE observed_vlan
	ADD CONSTRAINT "OBSERVED_VLAN_PK" PRIMARY KEY (switch_id, network_id, vlan_id);

-- Convert old chassis/chassis_hw to new chassis/primary_name_association
INSERT INTO primary_name_association (hardware_entity_id, dns_record_id, creation_date)
	SELECT chassis.chassis_hw_id, chassis.system_id, system.creation_date
		FROM chassis, system
		WHERE chassis.system_id = system.id;
UPDATE chassis_hw SET comments = (SELECT comments FROM chassis
					WHERE chassis.chassis_hw_id = chassis_hw.hardware_entity_id)
	WHERE comments IS NULL;
DROP TABLE chassis;
ALTER TABLE chassis_hw RENAME TO chassis;
ALTER TABLE chassis RENAME CONSTRAINT "CHASSIS_HW_PK" TO "CHASSIS_PK";
ALTER TABLE chassis RENAME CONSTRAINT "CHASSIS_HW_FK" TO "CHASSIS_HW_ENT_FK";
ALTER TABLE chassis RENAME CONSTRAINT "CHASSIS_HW_HW_ENT_ID_NN" TO "CHASSIS_HW_ENT_ID_NN";
ALTER INDEX "CHASSIS_HW_PK" RENAME TO "CHASSIS_PK";

-- Convert old switch/switch_hw to new switch/primary_name_association
INSERT INTO primary_name_association (hardware_entity_id, dns_record_id, creation_date)
	SELECT switch.switch_id, switch.id, system.creation_date
		FROM switch, system
		WHERE switch.id = system.id;
ALTER TABLE switch_hw ADD switch_type VARCHAR2(16);
UPDATE switch_hw SET switch_type = (SELECT switch_type FROM switch
					WHERE switch.switch_id = switch_hw.hardware_entity_id);
UPDATE switch_hw SET comments = (SELECT comments FROM switch
					WHERE switch.switch_id = switch_hw.hardware_entity_id)
	WHERE comments IS NULL;
DROP TABLE switch;
ALTER TABLE switch_hw RENAME TO switch;
ALTER TABLE switch RENAME CONSTRAINT "SWITCH_HW_PK" TO "SWITCH_PK";
ALTER TABLE switch RENAME CONSTRAINT "SWITCH_HW_HW_ENT_ID_NN" TO "SWITCH_HW_ENT_ID_NN";
ALTER TABLE switch RENAME CONSTRAINT "SWITCH_HW_LAST_POLL_NN" TO "SWITCH_LAST_POLL_NN";
ALTER TABLE switch
	MODIFY (switch_type CONSTRAINT "SWITCH_SWITCH_TYPE_NN" NOT NULL);
ALTER INDEX "TOR_SWITCH_HW_PK" RENAME TO "SWITCH_PK";

QUIT;
