INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'itsec', SYSDATE,
		'for ITSEC aquilon deployments');

QUIT;
