INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'template_admin', SYSDATE,
		'used for template development');

QUIT;
