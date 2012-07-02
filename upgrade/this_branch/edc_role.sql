INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'edc', SYSDATE,
		'used by EDC for filer deployments');

QUIT;
