ALTER TABLE interface ADD default_route INTEGER;
UPDATE interface SET default_route = bootable;
ALTER TABLE interface MODIFY (default_route CONSTRAINT "INTERFACE_DEFAULT_ROUTE_NN" NOT NULL);
ALTER TABLE interface ADD CONSTRAINT "IFACE_DEFAULT_ROUTE_CK" CHECK (default_route IN (0, 1));

QUIT;
