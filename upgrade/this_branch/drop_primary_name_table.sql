ALTER TABLE hardware_entity ADD primary_name_id NUMBER;
UPDATE hardware_entity SET primary_name_id =
	(SELECT dns_record_id
		FROM primary_name_association
		WHERE primary_name_association.hardware_entity_id = hardware_entity.id);
DROP TABLE primary_name_association;
