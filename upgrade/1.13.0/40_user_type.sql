CREATE SEQUENCE user_type_id_seq;

CREATE TABLE user_type (
	id INTEGER NOT NULL,
	name VARCHAR2(64 CHAR) NOT NULL,
	creation_date DATE NOT NULL,
	comments VARCHAR2(255 CHAR),
	CONSTRAINT user_type_pk PRIMARY KEY (id),
	CONSTRAINT user_type_name_uk UNIQUE (name)
);

INSERT INTO user_type (id, name, creation_date, comments)
	VALUES (user_type_id_seq.nextval, 'human', SYSDATE, 'Human users');

ALTER TABLE userinfo ADD type_id INTEGER;
ALTER TABLE userinfo ADD CONSTRAINT userinfo_user_type_fk FOREIGN KEY(type_id) REFERENCES user_type (id);
UPDATE userinfo SET type_id = user_type_id_seq.currval;
ALTER TABLE userinfo MODIFY (type_id CONSTRAINT userinfo_type_id_nn NOT NULL);

