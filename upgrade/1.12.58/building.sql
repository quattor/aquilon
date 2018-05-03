ALTER TABLE building ADD netdev_rack INTEGER;
UPDATE building SET netdev_rack = 0;
ALTER TABLE building MODIFY (netdev_rack INTEGER CONSTRAINT building_netdev_rack_nn NOT NULL);
ALTER TABLE building ADD CONSTRAINT building_netdev_rack_ck CHECK (netdev_rack IN (0, 1));

QUIT;
