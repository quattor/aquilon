CREATE TABLE personality_cluster_info (
	id INTEGER CONSTRAINT personality_cluster_info_id_nn NOT NULL,
	cluster_type VARCHAR2(16 CHAR) CONSTRAINT pers_clstr_cluster_type_nn NOT NULL,
	creation_date DATE CONSTRAINT pers_clstr_creation_date_nn NOT NULL,
	personality_stage_id INTEGER CONSTRAINT pers_clstr_pers_st_id_nn NOT NULL,
	CONSTRAINT personality_cluster_info_pk PRIMARY KEY (id),
	CONSTRAINT pers_clstr_pc_uk UNIQUE (personality_stage_id, cluster_type),
	CONSTRAINT pers_clstr_pers_st_fk FOREIGN KEY (personality_stage_id) REFERENCES personality_stage (id) ON DELETE CASCADE
);

CREATE TABLE personality_esx_cluster_info (
	personality_cluster_info_id INTEGER CONSTRAINT pers_esxclstr_pers_clstr_id_nn NOT NULL,
	vmhost_capacity_function VARCHAR2(255 CHAR),
	CONSTRAINT pers_esxclstr_pers_clstr_fk FOREIGN KEY (personality_cluster_info_id) REFERENCES personality_cluster_info (id) ON DELETE CASCADE,
	CONSTRAINT pers_esxclstr_pk PRIMARY KEY (personality_cluster_info_id)
);

CREATE SEQUENCE pers_clstr_id_seq;

QUIT;
