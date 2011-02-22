ALTER TABLE address_assignment ADD network_id INTEGER;
ALTER TABLE address_assignment
	ADD CONSTRAINT "ADDRESS_ASSIGNMENT_NETWORK_FK" FOREIGN KEY (network_id) REFERENCES network (id) ON DELETE SET NULL;


-- This takes about 25 minutes:
-- UPDATE address_assignment SET network_id = (SELECT network.id FROM network
--	WHERE address_assignment.ip >= network.ip AND address_assignment.ip <= network.ip + POWER(2, 32 - network.cidr))
-- The following procedure does the same in about 5 minutes
DECLARE
	CURSOR net_curs IS SELECT id, ip, cidr FROM network;
	net_rec net_curs%ROWTYPE;
	count INTEGER;
BEGIN
	-- DBMS_OUTPUT.PUT_LINE('Updating address assignments, it will take a few minutes');
	OPEN net_curs;
	LOOP
		FETCH net_curs INTO net_rec;
		EXIT WHEN net_curs%NOTFOUND;
		UPDATE address_assignment SET network_id = net_rec.id WHERE
			address_assignment.ip >= net_rec.ip AND
			address_assignment.ip <= net_rec.ip + POWER(2, 32 - net_rec.cidr);
	END LOOP;
	CLOSE net_curs;
END;
/

QUIT;
