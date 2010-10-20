ALTER TABLE network ADD broadcast INTEGER;

UPDATE network SET broadcast = ip + POWER(2, 32 - cidr) - 1;

ALTER TABLE network MODIFY (broadcast CONSTRAINT "NETWORK_BROADCAST_NN" NOT NULL);
