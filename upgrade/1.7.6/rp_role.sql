INSERT INTO role (id, name, creation_date, comments)
	VALUES (role_id_seq.nextval, 'resource_pool', SYSDATE,
		'commands needed by the resource pool manager');

QUIT;
