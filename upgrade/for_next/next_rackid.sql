ALTER TABLE building ADD next_rackid NUMBER(8);
UPDATE building SET next_rackid=2;
ALTER TABLE building MODIFY (next_rackid CONSTRAINT building_next_rackid_nn NOT NULL);

QUIT;