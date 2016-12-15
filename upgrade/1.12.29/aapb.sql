CREATE TABLE priority_list (
	resource_id INTEGER CONSTRAINT priority_list_resource_id_nn NOT NULL,
	CONSTRAINT priority_list_pk PRIMARY KEY (resource_id),
	CONSTRAINT priority_list_resource_fk FOREIGN KEY (resource_id) REFERENCES "resource" (id)
);

CREATE TABLE member_priority (
	priority_list_id INTEGER CONSTRAINT member_priority_pl_id_nn NOT NULL,
	member_id INTEGER CONSTRAINT member_priority_member_id_nn NOT NULL,
	priority INTEGER CONSTRAINT member_priority_priority_nn NOT NULL,
	creation_date DATE CONSTRAINT member_priority_cr_date_nn NOT NULL,
	CONSTRAINT member_priority_member_fk FOREIGN KEY (member_id) REFERENCES host_cluster_member (host_id) ON DELETE CASCADE,
	CONSTRAINT member_priority_pk PRIMARY KEY (priority_list_id, member_id),
	CONSTRAINT member_priority_pl_fk FOREIGN KEY (priority_list_id) REFERENCES priority_list (resource_id) ON DELETE CASCADE
);

CREATE INDEX member_priority_member_idx ON member_priority (member_id);

QUIT;
