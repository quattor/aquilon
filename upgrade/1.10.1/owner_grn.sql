-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE personality ADD owner_eon_id INTEGER;
ALTER TABLE personality ADD CONSTRAINT personality_owner_grn_fk FOREIGN KEY (owner_eon_id) REFERENCES grn (eon_id);
-- XXX Personalities with multiple GRNs will have to be fixed up later
DECLARE
	pers_rec personality%ROWTYPE;
	eon_id grn.eon_id%TYPE;

	CURSOR pers_curs IS
		SELECT * FROM personality
		FOR UPDATE OF personality.owner_eon_id;
	CURSOR grn_curs(pers_id IN personality_grn_map.personality_id%TYPE) IS
		SELECT eon_id FROM personality_grn_map WHERE personality_id = pers_id;
BEGIN
	OPEN pers_curs;
	LOOP
		FETCH pers_curs INTO pers_rec;
		EXIT WHEN pers_curs%NOTFOUND;

		OPEN grn_curs(pers_rec.id);
		FETCH grn_curs INTO eon_id;

		IF grn_curs%NOTFOUND THEN
			dbms_output.put_line('Missing GRN for personality ' || pers_rec.name);
			-- XXX Figure out a proper default GRN
			UPDATE personality SET owner_eon_id = 6980 WHERE CURRENT OF pers_curs;
		ELSE
			UPDATE personality SET owner_eon_id = eon_id WHERE CURRENT OF pers_curs;
			FETCH grn_curs INTO eon_id;
			IF NOT grn_curs%NOTFOUND THEN
				dbms_output.put_line('Multiple GRNs for personality ' || pers_rec.name);
			END IF;
		END IF;
		CLOSE grn_curs;
	END LOOP;
	CLOSE pers_curs;
END;
/

ALTER TABLE personality MODIFY (owner_eon_id CONSTRAINT personality_owner_eon_id_nn NOT NULL);

ALTER TABLE host ADD owner_eon_id INTEGER;
ALTER TABLE host ADD CONSTRAINT host_owner_grn_fk FOREIGN KEY (owner_eon_id) REFERENCES grn (eon_id);
DECLARE
	host_rec host%ROWTYPE;
	eon_id grn.eon_id%TYPE;

	CURSOR host_curs IS
		SELECT * FROM host
		FOR UPDATE OF host.owner_eon_id;
	CURSOR primary_name(host_id IN host.machine_id%TYPE) IS
		SELECT fqdn.name short, dns_domain.name domain
		FROM fqdn, dns_domain, dns_record, machine, hardware_entity
		WHERE machine.machine_id = host_id AND
			hardware_entity.id = machine.machine_id AND
			hardware_entity.primary_name_id = dns_record.id AND
			dns_record.fqdn_id = fqdn.id AND
			fqdn.dns_domain_id = dns_domain.id;
	CURSOR grn_curs(hostid IN host.machine_id%TYPE) IS
		SELECT eon_id FROM host_grn_map WHERE host_grn_map.host_id = hostid;
	CURSOR pers_curs(pers_id IN host.machine_id%TYPE) IS
		SELECT personality.owner_eon_id FROM personality
		WHERE personality.id = pers_id;

	primary_rec primary_name%ROWTYPE;
BEGIN
	OPEN host_curs;
	LOOP
		FETCH host_curs INTO host_rec;
		EXIT WHEN host_curs%NOTFOUND;

		OPEN grn_curs(host_rec.machine_id);
		FETCH grn_curs INTO eon_id;
		IF grn_curs%NOTFOUND THEN
			OPEN pers_curs(host_rec.personality_id);
			FETCH pers_curs INTO eon_id;
			CLOSE pers_curs;
			UPDATE host SET owner_eon_id = eon_id WHERE CURRENT OF host_curs;
		ELSE
			UPDATE host SET owner_eon_id = eon_id WHERE CURRENT OF host_curs;
			FETCH grn_curs INTO eon_id;
			IF NOT grn_curs%NOTFOUND THEN
				OPEN primary_name(host_rec.machine_id);
				FETCH primary_name INTO primary_rec;
				dbms_output.put_line('Multiple GRNs for host ' || primary_rec.short || '.' || primary_rec.domain);
				CLOSE primary_name;
			END IF;
		END IF;
		CLOSE grn_curs;
	END LOOP;
	CLOSE host_curs;
END;
/
ALTER TABLE host MODIFY (owner_eon_id CONSTRAINT host_owner_eon_id_nn NOT NULL);

QUIT;
