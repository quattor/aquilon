CREATE SEQUENCE entit_type_id_seq;

CREATE TABLE entit_type (
	id INTEGER NOT NULL,
	name VARCHAR2(64 CHAR) NOT NULL,
	to_grn SMALLINT NOT NULL,
	creation_date DATE NOT NULL,
	comments VARCHAR2(255 CHAR),
	CONSTRAINT entit_type_pk PRIMARY KEY (id),
	CONSTRAINT entit_type_name_uk UNIQUE (name),
	CONSTRAINT entit_type_to_grn_ck CHECK (to_grn IN (0, 1))
);

CREATE TABLE entit_type_user_type_map (
	entitlement_type_id INTEGER NOT NULL,
	user_type_id INTEGER NOT NULL,
	CONSTRAINT entit_type_user_type_map_pk PRIMARY KEY (entitlement_type_id, user_type_id),
	CONSTRAINT entyp_usrtyp_map_entit_type_fk FOREIGN KEY(entitlement_type_id) REFERENCES entit_type (id) ON DELETE CASCADE,
	CONSTRAINT entyp_usrtyp_map_user_type_fk FOREIGN KEY(user_type_id) REFERENCES user_type (id) ON DELETE CASCADE
);

CREATE INDEX entyp_usrtyp_map_enttyp_idx ON entit_type_user_type_map (entitlement_type_id);
CREATE INDEX entyp_usrtyp_map_usrtyp_idx ON entit_type_user_type_map (user_type_id);

