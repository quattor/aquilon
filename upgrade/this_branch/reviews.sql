CREATE TABLE review (
	source_id INTEGER CONSTRAINT review_source_id_nn NOT NULL,
	target_id INTEGER CONSTRAINT review_target_id_nn NOT NULL,
	commit_id VARCHAR2(40 CHAR) CONSTRAINT review_commit_id_nn NOT NULL,
	testing_url VARCHAR2(255 CHAR),
	target_commit_id VARCHAR2(40 CHAR),
	tested INTEGER,
	review_url VARCHAR2(255 CHAR),
	approved INTEGER,
	CONSTRAINT review_branch_fk FOREIGN KEY (source_id) REFERENCES branch (id) ON DELETE CASCADE,
	CONSTRAINT review_domain_fk FOREIGN KEY (target_id) REFERENCES domain (branch_id) ON DELETE CASCADE,
	CONSTRAINT review_tested_ck CHECK (tested IN (0, 1)),
	CONSTRAINT review_approved_ck CHECK (approved IN (0, 1)),
	CONSTRAINT review_pk PRIMARY KEY (source_id, target_id)
);

CREATE INDEX review_target_idx ON review (target_id);

QUIT;
