INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'aqweb', SYSDATE,
		'role for the bootserver and broker webserver proid');

QUIT;
