ALTER TABLE a_record ADD reverse_ptr_id INTEGER;
ALTER TABLE a_record ADD CONSTRAINT a_record_reverse_fk FOREIGN KEY (reverse_ptr_id) REFERENCES fqdn (id);

SET serveroutput on;

DECLARE
	CURSOR addr_curs IS SELECT a_record.dns_record_id, pri_fqdn.id AS pri_fqdn_id
		FROM a_record
			JOIN dns_record ON a_record.dns_record_id = dns_record.id,
			fqdn,
			address_assignment
			JOIN interface ON address_assignment.interface_id = interface.id
			JOIN hardware_entity ON interface.hardware_entity_id = hardware_entity.id
			JOIN dns_record pri_dns_record ON hardware_entity.primary_name_id = pri_dns_record.id
			JOIN a_record pri_a_record ON pri_dns_record.id = pri_a_record.dns_record_id
			JOIN fqdn pri_fqdn ON pri_dns_record.fqdn_id = pri_fqdn.id
		WHERE a_record.ip = address_assignment.ip
			AND a_record.network_id = address_assignment.network_id
			AND dns_record.fqdn_id = fqdn.id
			AND fqdn.dns_environment_id = address_assignment.dns_environment_id
			AND address_assignment.service_address_id IS NULL
			AND interface.interface_type != 'management'
			AND fqdn.id != pri_fqdn.id
		FOR UPDATE OF a_record.reverse_ptr_id;
	cnt NUMBER;
BEGIN
	cnt := 0;
	FOR addr IN addr_curs LOOP
		UPDATE a_record SET reverse_ptr_id = addr.pri_fqdn_id WHERE CURRENT OF addr_curs;
		cnt := cnt + 1;
	END LOOP;
	dbms_output.put_line('Converted ' || TO_CHAR(cnt) || ' addresses');
END;
/

COMMIT;

QUIT;
