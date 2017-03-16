-- a_record
ALTER TABLE a_record ADD new_ip RAW(16);
UPDATE a_record SET new_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN ip >= 2147483648 THEN ip - 4294967296 ELSE ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
DROP INDEX a_record_network_ip_idx;
ALTER TABLE a_record DROP COLUMN ip;
ALTER TABLE a_record RENAME COLUMN new_ip TO ip;
ALTER TABLE a_record MODIFY (ip CONSTRAINT a_record_ip_nn NOT NULL);
CREATE INDEX a_record_network_ip_idx ON a_record (network_id, ip);

-- addess_assignment
ALTER TABLE address_assignment ADD new_ip RAW(16);
UPDATE address_assignment SET new_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN ip >= 2147483648 THEN ip - 4294967296 ELSE ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
ALTER TABLE address_assignment DROP CONSTRAINT address_assignment_iface_ip_uk;
DROP INDEX address_assignment_iface_ip_uk;
DROP INDEX addr_assign_network_ip_idx;
ALTER TABLE address_assignment DROP COLUMN ip;
ALTER TABLE address_assignment RENAME COLUMN new_ip TO ip;
ALTER TABLE address_assignment MODIFY (ip CONSTRAINT address_assignment_ip_nn NOT NULL);
ALTER TABLE address_assignment ADD CONSTRAINT address_assignment_iface_ip_uk UNIQUE (interface_id, ip);
CREATE INDEX addr_assign_network_ip_idx ON address_assignment (network_id, ip);

-- network
ALTER TABLE network ADD new_ip RAW(16);
UPDATE network SET new_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN ip >= 2147483648 THEN ip - 4294967296 ELSE ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
ALTER TABLE network DROP CONSTRAINT network_net_env_ip_uk;
ALTER TABLE network DROP CONSTRAINT network_cidr_ck;
DROP INDEX network_net_env_ip_uk;
ALTER TABLE network DROP COLUMN ip;
ALTER TABLE network RENAME COLUMN new_ip TO ip;
ALTER TABLE network MODIFY (ip CONSTRAINT network_ip_nn NOT NULL);
ALTER TABLE network ADD CONSTRAINT network_net_env_ip_uk UNIQUE (network_environment_id, ip);
ALTER TABLE network ADD CONSTRAINT network_cidr_ip_ck
	CHECK (cidr >= 1 AND cidr <= CASE WHEN (ip >= HEXTORAW('00000000000000000000ffff00000000') AND ip <= HEXTORAW('00000000000000000000ffffffffffff')) THEN 32 ELSE 128 END);

-- router_address
ALTER TABLE router_address ADD new_ip RAW(16);
UPDATE router_address SET new_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN ip >= 2147483648 THEN ip - 4294967296 ELSE ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
ALTER TABLE router_address DROP CONSTRAINT router_address_pk;
DROP INDEX router_address_pk;
ALTER TABLE router_address DROP COLUMN ip;
ALTER TABLE router_address RENAME COLUMN new_ip TO ip;
ALTER TABLE router_address MODIFY (ip CONSTRAINT router_address_ip_nn NOT NULL);
ALTER TABLE router_address ADD CONSTRAINT router_address_pk PRIMARY KEY (network_id, ip);

-- static_route
ALTER TABLE static_route ADD new_dest_ip RAW(16);
ALTER TABLE static_route ADD new_gateway_ip RAW(16);
UPDATE static_route SET new_dest_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN dest_ip >= 2147483648 THEN dest_ip - 4294967296 ELSE dest_ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
UPDATE static_route SET new_gateway_ip = UTL_RAW.OVERLAY(UTL_RAW.CAST_FROM_BINARY_INTEGER(CASE WHEN gateway_ip >= 2147483648 THEN gateway_ip - 4294967296 ELSE gateway_ip END), HEXTORAW('00000000000000000000ffff00000000'), 13);
DROP INDEX static_route_gw_network_ip_idx;
ALTER TABLE static_route DROP COLUMN dest_ip;
ALTER TABLE static_route DROP COLUMN gateway_ip;
ALTER TABLE static_route RENAME COLUMN new_dest_ip TO dest_ip;
ALTER TABLE static_route RENAME COLUMN new_gateway_ip TO gateway_ip;
ALTER TABLE static_route MODIFY (dest_ip CONSTRAINT static_route_dest_ip_nn NOT NULL);
ALTER TABLE static_route MODIFY (gateway_ip CONSTRAINT static_route_gateway_ip_nn NOT NULL);
CREATE INDEX static_route_gw_network_ip_idx ON static_route (network_id, gateway_ip);

QUIT;
