INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'secadmin', SYSDATE,
		'used by Secadmins');

QUIT;
