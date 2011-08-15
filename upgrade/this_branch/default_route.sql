ALTER TABLE interface ADD default_route INTEGER;
UPDATE interface SET default_route = bootable;

-- All transit interfaces of zebra hosts should be providers of the default route
UPDATE interface SET default_route = 1 WHERE interface.id IN (
	SELECT interface.id
	FROM interface JOIN
		address_assignment ON interface.id = address_assignment.interface_id
	WHERE address_assignment.usage = 'zebra' AND
		address_assignment.label = 'hostname'
);

ALTER TABLE interface MODIFY (default_route CONSTRAINT "INTERFACE_DEFAULT_ROUTE_NN" NOT NULL);
ALTER TABLE interface ADD CONSTRAINT "IFACE_DEFAULT_ROUTE_CK" CHECK (default_route IN (0, 1));

QUIT;
