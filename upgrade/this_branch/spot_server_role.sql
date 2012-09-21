INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'spot_server', SYSDATE,
		'used by SPOT servers');

QUIT;
