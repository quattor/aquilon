CREATE TABLE entit_archetype_grn_map (
	type_id INTEGER NOT NULL,
	archetype_id INTEGER NOT NULL,
	host_environment_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	eon_id INTEGER NOT NULL,
	CONSTRAINT entit_archetype_grn_map_pk PRIMARY KEY (type_id, archetype_id, host_environment_id, location_id, eon_id),
	CONSTRAINT ent_arch_grn_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_arch_grn_map_archetype_fk FOREIGN KEY(archetype_id) REFERENCES archetype (id) ON DELETE CASCADE,
	CONSTRAINT ent_arch_grn_map_host_env_fk FOREIGN KEY(host_environment_id) REFERENCES host_environment (id) ON DELETE CASCADE,
	CONSTRAINT ent_arch_grn_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT entit_archetype_grn_map_grn_fk FOREIGN KEY(eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE
);

CREATE INDEX ent_arch_grn_map_grant_idx ON entit_archetype_grn_map (type_id, eon_id);
CREATE INDEX ent_arch_grn_map_match_idx ON entit_archetype_grn_map (type_id, archetype_id, host_environment_id, location_id);


CREATE TABLE entit_archetype_user_map (
	type_id INTEGER NOT NULL,
	archetype_id INTEGER NOT NULL,
	host_environment_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	CONSTRAINT entit_archetype_user_map_pk PRIMARY KEY (type_id, archetype_id, host_environment_id, location_id, user_id),
	CONSTRAINT ent_arch_usr_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_arch_usr_map_archetype_fk FOREIGN KEY(archetype_id) REFERENCES archetype (id) ON DELETE CASCADE,
	CONSTRAINT ent_arch_usr_map_host_env_fk FOREIGN KEY(host_environment_id) REFERENCES host_environment (id) ON DELETE CASCADE,
	CONSTRAINT ent_arch_usr_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT ent_arch_usr_map_userinfo_fk FOREIGN KEY(user_id) REFERENCES userinfo (id) ON DELETE CASCADE
);

CREATE INDEX ent_arch_usr_map_grant_idx ON entit_archetype_user_map (type_id, user_id);
CREATE INDEX ent_arch_usr_map_match_idx ON entit_archetype_user_map (type_id, archetype_id, host_environment_id, location_id);


CREATE TABLE entit_cluster_grn_map (
	type_id INTEGER NOT NULL,
	cluster_id INTEGER NOT NULL,
	eon_id INTEGER NOT NULL,
	CONSTRAINT entit_cluster_grn_map_pk PRIMARY KEY (type_id, cluster_id, eon_id),
	CONSTRAINT entit_cluster_grn_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT entit_cluster_grn_map_clstr_fk FOREIGN KEY(cluster_id) REFERENCES clstr (id) ON DELETE CASCADE,
	CONSTRAINT entit_cluster_grn_map_grn_fk FOREIGN KEY(eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE
);

CREATE INDEX ent_clstr_grn_map_match_idx ON entit_cluster_grn_map (type_id, cluster_id);
CREATE INDEX ent_clstr_grn_map_grant_idx ON entit_cluster_grn_map (type_id, eon_id);


CREATE TABLE entit_cluster_user_map (
	type_id INTEGER NOT NULL,
	cluster_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	CONSTRAINT entit_cluster_user_map_pk PRIMARY KEY (type_id, cluster_id, user_id),
	CONSTRAINT entit_cluster_user_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_clstr_usr_map_clstr_fk FOREIGN KEY(cluster_id) REFERENCES clstr (id) ON DELETE CASCADE,
	CONSTRAINT ent_clstr_usr_map_userinfo_fk FOREIGN KEY(user_id) REFERENCES userinfo (id) ON DELETE CASCADE
);

CREATE INDEX ent_clstr_usr_map_grant_idx ON entit_cluster_user_map (type_id, user_id);
CREATE INDEX ent_clstr_usr_map_match_idx ON entit_cluster_user_map (type_id, cluster_id);


CREATE TABLE entit_grn_grn_map (
	type_id INTEGER NOT NULL,
	target_eon_id INTEGER NOT NULL,
	host_environment_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	eon_id INTEGER NOT NULL,
	CONSTRAINT entit_grn_grn_map_pk PRIMARY KEY (type_id, target_eon_id, host_environment_id, location_id, eon_id),
	CONSTRAINT entit_grn_grn_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_grn_grn_map_target_grn_fk FOREIGN KEY(target_eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_grn_map_host_env_fk FOREIGN KEY(host_environment_id) REFERENCES host_environment (id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_grn_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_grn_map_grn_fk FOREIGN KEY(eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE
);

CREATE INDEX entit_grn_grn_map_match_idx ON entit_grn_grn_map (type_id, target_eon_id, host_environment_id, location_id);
CREATE INDEX entit_grn_grn_map_grant_idx ON entit_grn_grn_map (type_id, eon_id);


CREATE TABLE entit_grn_user_map (
	type_id INTEGER NOT NULL,
	target_eon_id INTEGER NOT NULL,
	host_environment_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	CONSTRAINT entit_grn_user_map_pk PRIMARY KEY (type_id, target_eon_id, host_environment_id, location_id, user_id),
	CONSTRAINT entit_grn_user_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_grn_usr_map_target_grn_fk FOREIGN KEY(target_eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_user_map_host_env_fk FOREIGN KEY(host_environment_id) REFERENCES host_environment (id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_user_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT entit_grn_user_map_userinfo_fk FOREIGN KEY(user_id) REFERENCES userinfo (id) ON DELETE CASCADE
);

CREATE INDEX entit_grn_user_map_grant_idx ON entit_grn_user_map (type_id, user_id);
CREATE INDEX entit_grn_user_map_match_idx ON entit_grn_user_map (type_id, target_eon_id, host_environment_id, location_id);


CREATE TABLE entit_host_grn_map (
	type_id INTEGER NOT NULL,
	host_id INTEGER NOT NULL,
	eon_id INTEGER NOT NULL,
	CONSTRAINT entit_host_grn_map_pk PRIMARY KEY (type_id, host_id, eon_id),
	CONSTRAINT entit_host_grn_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT entit_host_grn_map_host_fk FOREIGN KEY(host_id) REFERENCES host (hardware_entity_id) ON DELETE CASCADE,
	CONSTRAINT entit_host_grn_map_grn_fk FOREIGN KEY(eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE
);

CREATE INDEX entit_host_grn_map_match_idx ON entit_host_grn_map (type_id, host_id);
CREATE INDEX entit_host_grn_map_grant_idx ON entit_host_grn_map (type_id, eon_id);


CREATE TABLE entit_host_user_map (
	type_id INTEGER NOT NULL,
	host_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	CONSTRAINT entit_host_user_map_pk PRIMARY KEY (type_id, host_id, user_id),
	CONSTRAINT entit_host_user_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT entit_host_user_map_host_fk FOREIGN KEY(host_id) REFERENCES host (hardware_entity_id) ON DELETE CASCADE,
	CONSTRAINT ent_host_usr_map_userinfo_fk FOREIGN KEY(user_id) REFERENCES userinfo (id) ON DELETE CASCADE
);

CREATE INDEX entit_host_user_map_match_idx ON entit_host_user_map (type_id, host_id);
CREATE INDEX entit_host_user_map_grant_idx ON entit_host_user_map (type_id, user_id);


CREATE TABLE entit_personality_grn_map (
	type_id INTEGER NOT NULL,
	personality_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	eon_id INTEGER NOT NULL,
	CONSTRAINT entit_personality_grn_map_pk PRIMARY KEY (type_id, personality_id, location_id, eon_id),
	CONSTRAINT ent_pers_grn_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_pers_grn_map_pers_fk FOREIGN KEY(personality_id) REFERENCES personality (id) ON DELETE CASCADE,
	CONSTRAINT ent_pers_grn_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT ent_pers_grn_map_grn_fk FOREIGN KEY(eon_id) REFERENCES grn (eon_id) ON DELETE CASCADE
);

CREATE INDEX ent_pers_grn_map_grant_idx ON entit_personality_grn_map (type_id, eon_id);
CREATE INDEX ent_pers_grn_map_match_idx ON entit_personality_grn_map (type_id, personality_id, location_id);


CREATE TABLE entit_personality_user_map (
	type_id INTEGER NOT NULL,
	personality_id INTEGER NOT NULL,
	location_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	CONSTRAINT entit_personality_user_map_pk PRIMARY KEY (type_id, personality_id, location_id, user_id),
	CONSTRAINT ent_pers_usr_map_type_fk FOREIGN KEY(type_id) REFERENCES entit_type (id),
	CONSTRAINT ent_pers_usr_map_pers_fk FOREIGN KEY(personality_id) REFERENCES personality (id) ON DELETE CASCADE,
	CONSTRAINT ent_pers_usr_map_location_fk FOREIGN KEY(location_id) REFERENCES location (id) ON DELETE CASCADE,
	CONSTRAINT ent_pers_usr_map_userinfo_fk FOREIGN KEY(user_id) REFERENCES userinfo (id) ON DELETE CASCADE
);

CREATE INDEX ent_pers_usr_map_match_idx ON entit_personality_user_map (type_id, personality_id, location_id);
CREATE INDEX ent_pers_usr_map_grant_idx ON entit_personality_user_map (type_id, user_id);

