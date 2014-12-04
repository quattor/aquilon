CREATE SEQUENCE personality_stage_id_seq;

CREATE TABLE personality_stage (
	id INTEGER CONSTRAINT personality_stage_id_nn NOT NULL,
	personality_id INTEGER CONSTRAINT personality_stage_pers_id_nn NOT NULL,
	name VARCHAR2(8 CHAR) CONSTRAINT personality_stage_name_nn NOT NULL,
	CONSTRAINT personality_stage_pers_fk FOREIGN KEY (personality_id) REFERENCES personality (id) ON DELETE CASCADE,
	CONSTRAINT personality_stage_pk PRIMARY KEY (id),
	CONSTRAINT personality_stage_uk UNIQUE (personality_id, name)
);

ALTER TABLE host ADD personality_stage_id INTEGER;
ALTER TABLE clstr ADD personality_stage_id INTEGER;
ALTER TABLE param_holder ADD personality_stage_id INTEGER;
ALTER TABLE personality_grn_map ADD personality_stage_id INTEGER;
ALTER TABLE personality_service_list_item ADD personality_stage_id INTEGER;
ALTER TABLE personality_cluster_info ADD personality_stage_id INTEGER;
ALTER TABLE feature_link ADD personality_stage_id INTEGER;

DECLARE
	CURSOR pers_curs IS SELECT id FROM personality;
	pers_rec pers_curs%ROWTYPE;
	vers_id NUMBER;
BEGIN
	FOR pers_rec IN pers_curs LOOP
		INSERT INTO personality_stage (id, personality_id, name)
			VALUES (personality_stage_id_seq.NEXTVAL, pers_rec.id, 'current')
			RETURNING id INTO vers_id;
		UPDATE host SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE clstr SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE param_holder SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE personality_grn_map SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE personality_service_list_item SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE personality_cluster_info SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
		UPDATE feature_link SET personality_stage_id = vers_id WHERE personality_id = pers_rec.id;
	END LOOP;
END;
/

COMMIT;

ALTER TABLE host MODIFY (personality_stage_id INTEGER CONSTRAINT host_personality_stage_id_nn NOT NULL);
ALTER TABLE host ADD CONSTRAINT host_personality_stage_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id);
ALTER TABLE host DROP COLUMN personality_id;
CREATE INDEX host_personality_stage_idx ON host (personality_stage_id);

ALTER TABLE clstr MODIFY (personality_stage_id INTEGER CONSTRAINT clstr_personality_stage_id_nn NOT NULL);
ALTER TABLE clstr ADD CONSTRAINT clstr_personality_stage_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id);
ALTER TABLE clstr DROP COLUMN personality_id;
CREATE INDEX clstr_personality_stage_idx ON clstr (personality_stage_id);

ALTER TABLE param_holder ADD CONSTRAINT param_holder_pers_st_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE param_holder ADD CONSTRAINT param_holder_pers_st_uk UNIQUE (personality_stage_id);
ALTER TABLE param_holder DROP COLUMN personality_id;

ALTER TABLE personality_grn_map MODIFY (personality_stage_id INTEGER CONSTRAINT pers_grn_map_pers_st_id_nn NOT NULL);
ALTER TABLE personality_grn_map DROP CONSTRAINT personality_grn_map_pk;
ALTER TABLE personality_grn_map DROP COLUMN personality_id;
ALTER TABLE personality_grn_map ADD CONSTRAINT personality_grn_map_pers_st_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE personality_grn_map ADD CONSTRAINT personality_grn_map_pk
	PRIMARY KEY (personality_stage_id, eon_id, target);

ALTER TABLE personality_service_list_item MODIFY (personality_stage_id INTEGER CONSTRAINT psli_personality_stage_id_nn NOT NULL);
ALTER TABLE personality_service_list_item DROP CONSTRAINT psli_pk;
ALTER TABLE personality_service_list_item DROP COLUMN personality_id;
ALTER TABLE personality_service_list_item ADD CONSTRAINT psli_personality_stage_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE personality_service_list_item ADD CONSTRAINT psli_pk
	PRIMARY KEY (service_id, personality_stage_id);
CREATE INDEX psli_pers_st_idx ON personality_service_list_item (personality_stage_id);

ALTER TABLE personality_cluster_info MODIFY (personality_stage_id INTEGER CONSTRAINT pers_clstr_pers_st_id_nn NOT NULL);
ALTER TABLE personality_cluster_info DROP CONSTRAINT pers_clstr_pc_uk;
ALTER TABLE personality_cluster_info DROP COLUMN personality_id;
ALTER TABLE personality_cluster_info ADD CONSTRAINT pers_clstr_pers_st_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE personality_cluster_info ADD CONSTRAINT pers_clstr_pc_uk
	UNIQUE (personality_stage_id, cluster_type);

ALTER TABLE feature_link DROP CONSTRAINT feature_link_uk;
ALTER TABLE feature_link DROP COLUMN personality_id;
ALTER TABLE feature_link ADD CONSTRAINT feature_link_pers_st_fk
	FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE;
ALTER TABLE feature_link ADD CONSTRAINT feature_link_uk
	UNIQUE (feature_id, model_id, archetype_id, personality_stage_id, interface_name);
CREATE INDEX feature_link_pers_st_idx ON feature_link (personality_stage_id);

QUIT;
