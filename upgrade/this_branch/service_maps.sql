ALTER TABLE service_map ADD personality_id INTEGER;
ALTER TABLE service_map ADD CONSTRAINT service_map_personality_fk FOREIGN KEY (personality_id) REFERENCES personality (id);
CREATE INDEX service_map_personality_idx ON service_map (personality_id);

ALTER TABLE service_map DROP CONSTRAINT svc_map_loc_net_inst_uk;
DROP INDEX svc_map_loc_net_inst_uk;
ALTER TABLE service_map ADD CONSTRAINT service_map_uk UNIQUE (service_instance_id, personality_id, location_id, network_id);

INSERT INTO service_map (id, service_instance_id, personality_id, location_id, network_id, creation_date)
	SELECT service_map_id_seq.NEXTVAL, psm.service_instance_id, psm.personality_id, psm.location_id, psm.network_id, psm.creation_date
	FROM personality_service_map psm;

DROP TABLE personality_service_map;
DROP SEQUENCE pers_svc_map_id_seq;

QUIT;
