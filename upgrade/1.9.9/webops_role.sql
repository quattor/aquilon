INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'webops', SYSDATE,
		'used by Webops');

QUIT;
