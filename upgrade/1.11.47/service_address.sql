CREATE TABLE service_address_interface (
        service_address_id INTEGER CONSTRAINT srv_addr_iface_srv_addr_id_nn NOT NULL,
        interface_id INTEGER CONSTRAINT srv_addr_iface_interface_id_nn NOT NULL,
        CONSTRAINT service_address_interface_pk PRIMARY KEY (service_address_id, interface_id),
        CONSTRAINT srv_addr_iface_srv_addr_fk FOREIGN KEY(service_address_id) REFERENCES service_address (resource_id) ON DELETE CASCADE,
        CONSTRAINT srv_addr_iface_interface_fk FOREIGN KEY(interface_id) REFERENCES interface (id)
);

CREATE INDEX srv_addr_iface_iface_idx ON service_address_interface (interface_id);

DECLARE
	CURSOR iface_curs IS
		SELECT interface.id AS interface_id, service_address.resource_id AS service_address_id
		FROM interface
			JOIN address_assignment ON address_assignment.interface_id = interface.id
			JOIN service_address ON address_assignment.service_address_id = service_address.resource_id
			JOIN "resource" ON service_address.resource_id = "resource".id
			JOIN resholder ON "resource".holder_id = resholder.id
		WHERE resholder.holder_type = 'host';
	iface_rec iface_curs%ROWTYPE;
BEGIN
	FOR iface_rec IN iface_curs LOOP
		INSERT INTO service_address_interface (interface_id, service_address_id)
			VALUES (iface_rec.interface_id, iface_rec.service_address_id);
	END LOOP;
END;
/

ALTER TABLE address_assignment DROP COLUMN service_address_id;
DROP INDEX service_address_dns_record_idx;
ALTER TABLE service_address ADD CONSTRAINT service_address_dns_record_uk UNIQUE (dns_record_id);

QUIT;
