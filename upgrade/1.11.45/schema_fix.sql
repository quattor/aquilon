ALTER TABLE personality_service_list_item DROP CONSTRAINT psli_service_fk;
ALTER TABLE personality_service_list_item ADD CONSTRAINT psli_service_fk FOREIGN KEY (service_id) REFERENCES service (id);
ALTER TABLE personality_service_map DROP CONSTRAINT pers_svc_map_svc_inst_fk;
ALTER TABLE personality_service_map ADD CONSTRAINT pers_svc_map_svc_inst_fk FOREIGN KEY (service_instance_id) REFERENCES service_instance (id);
ALTER TABLE service_list_item DROP CONSTRAINT service_list_item_service_fk;
ALTER TABLE service_list_item ADD CONSTRAINT service_list_item_service_fk FOREIGN KEY (service_id) REFERENCES service (id);
ALTER TABLE personality MODIFY (id INTEGER);
ALTER TABLE personality MODIFY (archetype_id INTEGER);

QUIT;
