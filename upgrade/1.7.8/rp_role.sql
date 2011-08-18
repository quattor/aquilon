INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'winops_server', SYSDATE,
		'winops server support related commands');

QUIT;
