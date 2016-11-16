CREATE TABLE building_preference (
	a_id INTEGER CONSTRAINT building_preference_a_id_nn NOT NULL,
	b_id INTEGER CONSTRAINT building_preference_b_id_nn NOT NULL,
	archetype_id INTEGER CONSTRAINT building_preference_arch_id_nn NOT NULL,
	prefer_id INTEGER CONSTRAINT bldg_pref_prefer_id_nn NOT NULL,
	creation_date DATE CONSTRAINT building_preference_cr_date_nn NOT NULL,
	CONSTRAINT bldg_pref_a_b_prefer_ck CHECK (a_id < b_id AND (a_id = prefer_id OR b_id = prefer_id)),
	CONSTRAINT building_preference_bldg_a_fk FOREIGN KEY (a_id) REFERENCES building (id) ON DELETE CASCADE,
	CONSTRAINT building_preference_bldg_b_fk FOREIGN KEY (b_id) REFERENCES building (id) ON DELETE CASCADE,
	CONSTRAINT building_preference_prefer_fk FOREIGN KEY (prefer_id) REFERENCES building (id),
	CONSTRAINT building_preference_arch_fk FOREIGN KEY (archetype_id) REFERENCES archetype (id) ON DELETE CASCADE,
	CONSTRAINT building_preference_pk PRIMARY KEY (a_id, b_id, archetype_id)
);

CREATE INDEX building_preference_b_idx ON building_preference (b_id);
CREATE INDEX building_preference_prefer_idx ON building_preference (prefer_id);
CREATE INDEX building_preference_arch_idx ON building_preference (archetype_id);

QUIT;
