CREATE TABLE virtual_machine (
	resource_id INTEGER CONSTRAINT virtual_machine_resource_id_nn NOT NULL,
	machine_id INTEGER CONSTRAINT virtual_machine_machine_id_nn NOT NULL,
	CONSTRAINT virtual_machine_resource_fk FOREIGN KEY (resource_id) REFERENCES "resource" (id) ON DELETE CASCADE,
	CONSTRAINT virtual_machine_machine_fk FOREIGN KEY (machine_id) REFERENCES machine (machine_id) ON DELETE CASCADE,
	CONSTRAINT virtual_machine_pk PRIMARY KEY (resource_id)
);

-- Disable autocommit, abort if something goes wrong
SET autocommit off;
WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

VARIABLE cnt NUMBER;
DECLARE
	cluster_id clstr.id%TYPE;
	holder_id resholder.id%TYPE;
	creation_date "resource".creation_date%TYPE;
	resource_id "resource".id%TYPE;
	machine_label hardware_entity.label%TYPE;
	machine_id machine.machine_id%TYPE;
	cnt NUMBER;

	-- Get cluster IDs that do not have a resource holder but have a VM
	CURSOR missing_holder IS
		SELECT clstr.id FROM clstr
			LEFT OUTER JOIN resholder ON resholder.cluster_id = clstr.id
		WHERE resholder.id IS NULL AND EXISTS
			(
				SELECT 1 FROM machine_cluster_member
				WHERE machine_cluster_member.cluster_id = clstr.id
			);

	CURSOR vm_curs IS
		SELECT resholder.id AS holder_id,
			machine_cluster_member.machine_id,
			machine_cluster_member.creation_date,
			hardware_entity.label
		FROM machine_cluster_member JOIN machine ON machine.machine_id = machine_cluster_member.machine_id
			JOIN hardware_entity ON hardware_entity.id = machine.machine_id
			JOIN resholder ON resholder.cluster_id = machine_cluster_member.cluster_id;
BEGIN
	-- Ensure all clusters having VMs also have a resource holder object
	:cnt := 0;
	OPEN missing_holder;
	LOOP
		FETCH missing_holder INTO cluster_id;
		EXIT WHEN missing_holder%NOTFOUND;

		INSERT INTO resholder (id, holder_type, cluster_id) VALUES (resholder_seq.NEXTVAL, 'cluster', cluster_id);
		:cnt := :cnt + 1;
	END LOOP;
	CLOSE missing_holder;
	dbms_output.put_line('Added ' || TO_CHAR(:cnt) || ' resource holders');

	-- Convert the machine_cluster_member table to virtual_machine
	:cnt := 0;
	OPEN vm_curs;
	LOOP
		FETCH vm_curs INTO holder_id, machine_id, creation_date, machine_label;
		EXIT WHEN vm_curs%NOTFOUND;

		INSERT INTO "resource" (id, resource_type, name, creation_date, holder_id)
			VALUES (resource_seq.NEXTVAL, 'virtual_machine', machine_label, creation_date, holder_id)
			RETURNING id INTO resource_id;
		INSERT INTO virtual_machine (resource_id, machine_id)
			VALUES (resource_id, machine_id);
		:cnt := :cnt + 1;
	END LOOP;
	CLOSE vm_curs;
	dbms_output.put_line('Converted ' || TO_CHAR(:cnt) || ' virtual machines');
END;
/

COMMIT;

DROP TABLE machine_cluster_member;

QUIT;
