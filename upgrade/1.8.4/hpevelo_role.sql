INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'hpevelo', SYSDATE,
		'used to manage the HPE velocity lab');

QUIT;
