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

QUIT;
