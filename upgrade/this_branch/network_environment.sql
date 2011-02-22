CREATE SEQUENCE network_environment_id_seq;
CREATE TABLE network_environment (
	id INTEGER CONSTRAINT "NET_ENV_ID_NN" NOT NULL,
	name VARCHAR2(64 CHAR) CONSTRAINT "NET_ENV_NAME_NN" NOT NULL,
	location_id INTEGER,
	creation_date DATE CONSTRAINT "NET_ENV_CR_DATE_NN" NOT NULL,
	comments VARCHAR(255 CHAR),
	CONSTRAINT "NETWORK_ENVIRONMENT_PK" PRIMARY KEY (id),
	CONSTRAINT "NET_ENV_NAME_UK" UNIQUE (name),
	CONSTRAINT "NET_ENV_LOC_FK" FOREIGN KEY (location_id) REFERENCES location (id)
);

INSERT INTO network_environment (id, name, location_id, creation_date, comments)
	VALUES (network_environment_id_seq.NEXTVAL, 'internal', NULL,
		CURRENT_DATE, 'Morgan Stanley internal networks');

ALTER TABLE network ADD network_environment_id INTEGER;
UPDATE network SET network_environment_id =
	(SELECT id FROM network_environment WHERE name = 'internal');
ALTER TABLE network MODIFY (network_environment_id CONSTRAINT "NETWORK_NET_ENV_ID_NN" NOT NULL);
ALTER TABLE network
	ADD CONSTRAINT "NETWORK_NET_ENV_FK"
	FOREIGN KEY (network_environment_id) REFERENCES network_environment (id);
ALTER TABLE network DROP CONSTRAINT "NETWORK_IP_UK";
ALTER TABLE network ADD CONSTRAINT "NETWORK_NET_ENV_IP_UK" UNIQUE (network_environment_id, ip);

ALTER TABLE router_address DROP CONSTRAINT "ROUTER_ADDRESS_PK";
DROP INDEX "ROUTER_ADDRESS_PK";
ALTER TABLE router_address ADD CONSTRAINT "ROUTER_ADDRESS_PK" PRIMARY KEY (ip, network_id);

QUIT;
