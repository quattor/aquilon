CREATE TABLE cluster_group (
	id INTEGER CONSTRAINT cluster_group_id_nn NOT NULL,
	creation_date DATE CONSTRAINT cluster_group_creation_date_nn NOT NULL,
	CONSTRAINT cluster_group_pk PRIMARY KEY (id)
);

CREATE SEQUENCE cluster_group_id_seq;

CREATE TABLE cluster_group_member (
	cluster_group_id INTEGER CONSTRAINT clstr_grp_mmbr_clstr_grp_id_nn NOT NULL,
	cluster_id INTEGER CONSTRAINT clstr_grp_mmbr_cluster_id_nn NOT NULL,
	CONSTRAINT clstr_grp_mmbr_clstr_grp_fk FOREIGN KEY (cluster_group_id) REFERENCES cluster_group (id) ON DELETE CASCADE,
	CONSTRAINT clstr_grp_mmbr_cluster_uk UNIQUE (cluster_id),
	CONSTRAINT cluster_group_member_clstr_fk FOREIGN KEY (cluster_id) REFERENCES clstr (id) ON DELETE CASCADE,
	CONSTRAINT cluster_group_member_pk PRIMARY KEY (cluster_group_id, cluster_id)
);

QUIT;
