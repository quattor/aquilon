CREATE TABLE service_address (
	resource_id INTEGER CONSTRAINT srv_addr_resource_id_nn NOT NULL,
	dns_record_id INTEGER CONSTRAINT srv_addr_dns_record_id_nn NOT NULL,
	CONSTRAINT srv_addr_resource_fk FOREIGN KEY (resource_id) REFERENCES "resource" (id),
	CONSTRAINT srv_addr_arecord_fk FOREIGN KEY (dns_record_id) REFERENCES a_record (dns_record_id),
	CONSTRAINT service_address_pk PRIMARY KEY (resource_id)
);

ALTER TABLE address_assignment ADD service_address_id INTEGER;
ALTER TABLE address_assignment ADD CONSTRAINT addr_assign_srv_addr_id FOREIGN KEY (service_address_id) REFERENCES service_address (resource_id) ON DELETE CASCADE;

-- Disable autocommit, abort if something goes wrong
SET autocommit off;
WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

VARIABLE cnt NUMBER;
DECLARE
	srv_addr_id service_address.resource_id%TYPE;
	dns_rec_id a_record.dns_record_id%TYPE;
	host_id host.machine_id%TYPE;
	holder_id resholder.id%TYPE;
	cnt NUMBER;

	CURSOR addr_curs IS
		SELECT address_assignment.*, resholder.id AS holder_id FROM address_assignment
			JOIN interface ON interface.id = address_assignment.interface_id
			JOIN hardware_entity ON hardware_entity.id = interface.hardware_entity_id
			LEFT OUTER JOIN host ON host.machine_id = hardware_entity.id
			LEFT OUTER JOIN resholder ON resholder.host_id = host.machine_id
		WHERE address_assignment.usage = 'zebra'
		FOR UPDATE OF address_assignment.usage, address_assignment.service_address_id;

	addr_rec addr_curs%ROWTYPE;

	CURSOR srv_curs(dns_id IN service_address.dns_record_id%TYPE) IS
		SELECT service_address.resource_id FROM service_address WHERE service_address.dns_record_id = dns_id;

	-- Get host IDs that do not have a resource holder but have a zebra address
	CURSOR missing_holder IS
		SELECT host.machine_id FROM host
			JOIN machine ON machine.machine_id = host.machine_id
			LEFT OUTER JOIN resholder ON resholder.host_id = host.machine_id
		WHERE resholder.id IS NULL AND EXISTS
			(
				SELECT 1 FROM address_assignment
					JOIN interface ON address_assignment.interface_id = interface.id
				WHERE interface.hardware_entity_id = host.machine_id AND address_assignment.usage = 'zebra'
			);
BEGIN
	-- Ensure all hosts having a Zebra address also has a resource holder object
	:cnt := 0;
	OPEN missing_holder;
	LOOP
		FETCH missing_holder INTO host_id;
		EXIT WHEN missing_holder%NOTFOUND;

		INSERT INTO resholder (id, holder_type, host_id) VALUES (resholder_seq.NEXTVAL, 'host', host_id);
		:cnt := :cnt + 1;
	END LOOP;
	CLOSE missing_holder;
	dbms_output.put_line('Added ' || TO_CHAR(:cnt) || ' resource holders');

	:cnt := 0;
	OPEN addr_curs;
	LOOP
		FETCH addr_curs INTO addr_rec;
		EXIT WHEN addr_curs%NOTFOUND;

		-- This throws an exception either if there is no matching DNS record or if there are more than one
		SELECT a_record.dns_record_id INTO dns_rec_id FROM a_record
			WHERE a_record.ip = addr_rec.ip AND a_record.network_id = addr_rec.network_id;

		-- Fetch the resource object or create it if needed
		OPEN srv_curs(dns_rec_id);
		FETCH srv_curs INTO srv_addr_id;
		IF srv_curs%NOTFOUND THEN
			INSERT INTO "resource" (id, resource_type, name, creation_date, holder_id)
				VALUES (resource_seq.NEXTVAL, 'service_address', addr_rec.label,
					addr_rec.creation_date, addr_rec.holder_id)
				RETURNING id INTO srv_addr_id;
			INSERT INTO service_address (resource_id, dns_record_id)
				VALUES (srv_addr_id, dns_rec_id);
		END IF;
		CLOSE srv_curs;

		UPDATE address_assignment SET service_address_id = srv_addr_id WHERE CURRENT OF addr_curs;
		:cnt := :cnt + 1;
	END LOOP;
	CLOSE addr_curs;
	dbms_output.put_line('Converted ' || TO_CHAR(:cnt) || ' address assignments');
END;
/

SELECT COUNT(*) AS "Conversion failed" FROM address_assignment WHERE usage = 'zebra' AND service_address_id IS NULL;

ALTER TABLE address_assignment DROP COLUMN usage;

COMMIT;
QUIT;
