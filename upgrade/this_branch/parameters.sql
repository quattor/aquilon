ALTER TABLE parameter MODIFY (value CONSTRAINT parameter_value_nn NOT NULL);

ALTER TABLE parameter ADD holder_type VARCHAR2(16 CHAR);
ALTER TABLE parameter ADD personality_stage_id INTEGER;

UPDATE parameter SET holder_type = (SELECT holder_type FROM param_holder WHERE parameter.holder_id = param_holder.id);
ALTER TABLE parameter MODIFY (holder_type CONSTRAINT parameter_holder_type_nn NOT NULL);

UPDATE parameter SET personality_stage_id = (SELECT personality_stage_id FROM param_holder WHERE parameter.holder_id = param_holder.id);
ALTER TABLE parameter DROP COLUMN holder_id;

ALTER TABLE parameter ADD CONSTRAINT parameter_personality_stage_fk FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE parameter ADD CONSTRAINT parameter_personality_stage_uk UNIQUE (personality_stage_id);

DROP TABLE param_holder;
DROP SEQUENCE param_holder_id_seq;

QUIT;
