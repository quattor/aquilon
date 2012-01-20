ALTER TABLE hardware_entity ADD primary_name_id INTEGER;
UPDATE hardware_entity SET primary_name_id =
	(SELECT dns_record_id
		FROM primary_name_association
		WHERE primary_name_association.hardware_entity_id = hardware_entity.id);
DROP TABLE primary_name_association;
ALTER TABLE hardware_entity ADD CONSTRAINT "HW_ENT_PRI_NAME_FK" FOREIGN KEY (primary_name_id) REFERENCES dns_record (id);
