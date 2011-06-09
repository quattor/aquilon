ALTER TABLE interface ADD model_id INTEGER;

DECLARE
	id_value model.id%TYPE;
BEGIN
	INSERT INTO model (id, name, vendor_id, machine_type, creation_date)
		VALUES (model_id_seq.nextval, 'generic_nic',
			(SELECT id FROM vendor WHERE name = 'generic'),
			'nic', CURRENT_DATE)
		RETURNING id
		INTO id_value;

	UPDATE interface SET model_id = id_value;
END;
/

ALTER TABLE interface MODIFY (model_id CONSTRAINT "INTERFACE_MODEL_ID_NN" NOT NULL);

QUIT;
