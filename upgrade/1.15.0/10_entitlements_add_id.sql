CREATE SEQUENCE entitlement_id_seq;

CREATE TABLE entitlement (
	id INTEGER NOT NULL,
	CONSTRAINT entitlement_pk PRIMARY KEY (id)
);

ALTER TABLE entit_host_grn_map DROP CONSTRAINT entit_host_grn_map_pk DROP INDEX;
ALTER TABLE entit_host_grn_map ADD CONSTRAINT entit_host_grn_map_uk UNIQUE (type_id, host_id, eon_id);
ALTER TABLE entit_host_grn_map ADD id INTEGER;
UPDATE entit_host_grn_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_host_grn_map;
ALTER TABLE entit_host_grn_map MODIFY(id CONSTRAINT entit_host_grn_map_id_nn NOT NULL);
ALTER TABLE entit_host_grn_map ADD CONSTRAINT entit_host_grn_map_pk PRIMARY KEY (id);
ALTER TABLE entit_host_grn_map ADD CONSTRAINT entit_host_grn_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_host_user_map DROP CONSTRAINT entit_host_user_map_pk DROP INDEX;
ALTER TABLE entit_host_user_map ADD CONSTRAINT entit_host_user_map_uk UNIQUE (type_id, host_id, user_id);
ALTER TABLE entit_host_user_map ADD id INTEGER;
UPDATE entit_host_user_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_host_user_map;
ALTER TABLE entit_host_user_map MODIFY(id CONSTRAINT entit_host_grn_user_id_nn NOT NULL);
ALTER TABLE entit_host_user_map ADD CONSTRAINT entit_host_user_map_pk PRIMARY KEY (id);
ALTER TABLE entit_host_user_map ADD CONSTRAINT entit_host_user_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_cluster_grn_map DROP CONSTRAINT entit_cluster_grn_map_pk DROP INDEX;
ALTER TABLE entit_cluster_grn_map ADD CONSTRAINT entit_cluster_grn_map_uk UNIQUE (type_id, cluster_id, eon_id);
ALTER TABLE entit_cluster_grn_map ADD id INTEGER;
UPDATE entit_cluster_grn_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_cluster_grn_map;
ALTER TABLE entit_cluster_grn_map MODIFY(id CONSTRAINT entit_cluster_grn_map_id_nn NOT NULL);
ALTER TABLE entit_cluster_grn_map ADD CONSTRAINT entit_cluster_grn_map_pk PRIMARY KEY (id);
ALTER TABLE entit_cluster_grn_map ADD CONSTRAINT entit_cluster_grn_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_cluster_user_map DROP CONSTRAINT entit_cluster_user_map_pk DROP INDEX;
ALTER TABLE entit_cluster_user_map ADD CONSTRAINT entit_cluster_user_map_uk UNIQUE (type_id, cluster_id, user_id);
ALTER TABLE entit_cluster_user_map ADD id INTEGER;
UPDATE entit_cluster_user_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_cluster_user_map;
ALTER TABLE entit_cluster_user_map MODIFY(id CONSTRAINT entit_cluster_user_map_id_nn NOT NULL);
ALTER TABLE entit_cluster_user_map ADD CONSTRAINT entit_cluster_user_map_pk PRIMARY KEY (id);
ALTER TABLE entit_cluster_user_map ADD CONSTRAINT entit_cluster_user_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_personality_grn_map DROP CONSTRAINT entit_personality_grn_map_pk DROP INDEX;
ALTER TABLE entit_personality_grn_map ADD CONSTRAINT entit_personality_grn_map_uk UNIQUE (type_id, personality_id, location_id, eon_id);
ALTER TABLE entit_personality_grn_map ADD id INTEGER;
UPDATE entit_personality_grn_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_personality_grn_map;
ALTER TABLE entit_personality_grn_map MODIFY(id CONSTRAINT entit_pers_grn_map_id_nn NOT NULL);
ALTER TABLE entit_personality_grn_map ADD CONSTRAINT entit_personality_grn_map_pk PRIMARY KEY (id);
ALTER TABLE entit_personality_grn_map ADD CONSTRAINT entit_pers_grn_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_personality_user_map DROP CONSTRAINT entit_personality_user_map_pk DROP INDEX;
ALTER TABLE entit_personality_user_map ADD CONSTRAINT entit_personality_user_map_uk UNIQUE (type_id, personality_id, location_id, user_id);
ALTER TABLE entit_personality_user_map ADD id INTEGER;
UPDATE entit_personality_user_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_personality_user_map;
ALTER TABLE entit_personality_user_map MODIFY(id CONSTRAINT entit_pers_usr_map_id_nn NOT NULL);
ALTER TABLE entit_personality_user_map ADD CONSTRAINT entit_personality_user_map_pk PRIMARY KEY (id);
ALTER TABLE entit_personality_user_map ADD CONSTRAINT entit_pers_usr_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_archetype_grn_map DROP CONSTRAINT entit_archetype_grn_map_pk DROP INDEX;
ALTER TABLE entit_archetype_grn_map ADD CONSTRAINT entit_archetype_grn_map_uk UNIQUE (type_id, archetype_id, host_environment_id, location_id, eon_id);
ALTER TABLE entit_archetype_grn_map ADD id INTEGER;
UPDATE entit_archetype_grn_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_archetype_grn_map;
ALTER TABLE entit_archetype_grn_map MODIFY(id CONSTRAINT entit_archetype_grn_map_id_nn NOT NULL);
ALTER TABLE entit_archetype_grn_map ADD CONSTRAINT entit_archetype_grn_map_pk PRIMARY KEY (id);
ALTER TABLE entit_archetype_grn_map ADD CONSTRAINT entit_archetype_grn_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_archetype_user_map DROP CONSTRAINT entit_archetype_user_map_pk DROP INDEX;
ALTER TABLE entit_archetype_user_map ADD CONSTRAINT entit_archetype_user_map_uk UNIQUE (type_id, archetype_id, host_environment_id, location_id, user_id);
ALTER TABLE entit_archetype_user_map ADD id INTEGER;
UPDATE entit_archetype_user_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_archetype_user_map;
ALTER TABLE entit_archetype_user_map MODIFY(id CONSTRAINT entit_archetype_user_map_id_nn NOT NULL);
ALTER TABLE entit_archetype_user_map ADD CONSTRAINT entit_archetype_user_map_pk PRIMARY KEY (id);
ALTER TABLE entit_archetype_user_map ADD CONSTRAINT entit_archetype_user_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_grn_grn_map DROP CONSTRAINT entit_grn_grn_map_pk DROP INDEX;
ALTER TABLE entit_grn_grn_map ADD CONSTRAINT entit_grn_grn_map_uk UNIQUE (type_id, target_eon_id, host_environment_id, location_id, eon_id);
ALTER TABLE entit_grn_grn_map ADD id INTEGER;
UPDATE entit_grn_grn_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_grn_grn_map;
ALTER TABLE entit_grn_grn_map MODIFY(id CONSTRAINT entit_grn_grn_map_id_nn NOT NULL);
ALTER TABLE entit_grn_grn_map ADD CONSTRAINT entit_grn_grn_map_pk PRIMARY KEY (id);
ALTER TABLE entit_grn_grn_map ADD CONSTRAINT entit_grn_grn_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

ALTER TABLE entit_grn_user_map DROP CONSTRAINT entit_grn_user_map_pk DROP INDEX;
ALTER TABLE entit_grn_user_map ADD CONSTRAINT entit_grn_user_map_uk UNIQUE (type_id, target_eon_id, host_environment_id, location_id, user_id);
ALTER TABLE entit_grn_user_map ADD id INTEGER;
UPDATE entit_grn_user_map SET id = entitlement_id_seq.NEXTVAL;
INSERT INTO entitlement (id) SELECT id FROM entit_grn_user_map;
ALTER TABLE entit_grn_user_map MODIFY(id CONSTRAINT entit_grn_user_map_id_nn NOT NULL);
ALTER TABLE entit_grn_user_map ADD CONSTRAINT entit_grn_user_map_pk PRIMARY KEY (id);
ALTER TABLE entit_grn_user_map ADD CONSTRAINT entit_grn_user_map_id_fk FOREIGN KEY(id) REFERENCES entitlement (id) ON DELETE CASCADE;

