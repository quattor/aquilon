INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'mssb_unixops', SYSDATE,
		'used to manage legacy MSSB DNS entries');

QUIT;
