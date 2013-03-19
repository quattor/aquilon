ALTER TABLE personality_grn_map DROP CONSTRAINT pers_grn_map_personality_fk;
ALTER TABLE personality_grn_map ADD CONSTRAINT pers_grn_map_personality_fk FOREIGN KEY (personality_id) REFERENCES personality (id) ON DELETE CASCADE;

ALTER TABLE host_grn_map DROP CONSTRAINT host_grn_map_host_fk;
ALTER TABLE host_grn_map ADD CONSTRAINT host_grn_map_host_fk FOREIGN KEY (host_id) REFERENCES host (machine_id) ON DELETE CASCADE;

QUIT;
