ALTER TABLE observed_vlan RENAME CONSTRAINT "OBSERVED_VLAN_MAX_VLAN_ID" TO "OBSERVED_VLAN_MAX_VLAN_ID_CK";
ALTER TABLE observed_vlan RENAME CONSTRAINT "OBSERVED_VLAN_MIN_VLAN_ID" TO "OBSERVED_VLAN_MIN_VLAN_ID_CK";
ALTER TABLE vlan_info RENAME CONSTRAINT "VLAN_INFO_MAX_VLAN_ID" TO "VLAN_INFO_MAX_VLAN_ID_CK";
ALTER TABLE vlan_info RENAME CONSTRAINT "VLAN_INFO_MIN_VLAN_ID" TO "VLAN_INFO_MIN_VLAN_ID_CK";

-- Give real names to unnamed constraints
DECLARE
	name user_constraints.constraint_name%TYPE;
BEGIN
	-- Archetype
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'ARCHETYPE' AND
			cc.column_name = 'IS_COMPILEABLE';
	EXECUTE IMMEDIATE 'ALTER TABLE archetype RENAME CONSTRAINT ' || name || ' TO "ARCHETYPE_IS_COMPILEABLE_CK"';

	-- Branch
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'BRANCH' AND
			cc.column_name = 'IS_SYNC_VALID';
	EXECUTE IMMEDIATE 'ALTER TABLE branch RENAME CONSTRAINT ' || name || ' TO "BRANCH_IS_SYNC_VALID_CK"';
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'BRANCH' AND
			cc.column_name = 'AUTOSYNC';
	EXECUTE IMMEDIATE 'ALTER TABLE branch RENAME CONSTRAINT ' || name || ' TO "BRANCH_AUTOSYNC_CK"';

	-- Interface
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'INTERFACE' AND
			cc.column_name = 'BOOTABLE';
	EXECUTE IMMEDIATE 'ALTER TABLE interface RENAME CONSTRAINT ' || name || ' TO "IFACE_BOOTABLE_CK"';

	-- Network
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'NETWORK' AND
			cc.column_name = 'IS_DISCOVERABLE';
	EXECUTE IMMEDIATE 'ALTER TABLE network RENAME CONSTRAINT ' || name || ' TO "NETWORK_IS_DISCOVERABLE_CK"';
	SELECT c.constraint_name INTO name
		FROM user_constraints c, user_cons_columns cc
		WHERE c.constraint_name = cc.constraint_name AND
			c.generated = 'GENERATED NAME' AND
			c.table_name = 'NETWORK' AND
			cc.column_name = 'IS_DISCOVERED';
	EXECUTE IMMEDIATE 'ALTER TABLE network RENAME CONSTRAINT ' || name || ' TO "NETWORK_IS_DISCOVERED_CK"';
END;
/

ALTER TABLE metacluster RENAME CONSTRAINT "METACLUSTER_HA_CHECK" TO "METACLUSTER_HA_CK";

ALTER TABLE network RENAME CONSTRAINT "NET_IP_UK" TO "NETWORK_IP_UK";
ALTER TABLE network ADD CONSTRAINT "NETWORK_CIDR_CK" CHECK (cidr >= 1 AND cidr <= 32);

ALTER INDEX "NET_LOC_ID_IDX" RENAME TO "NETWORK_LOC_ID_IDX";
ALTER INDEX "NET_IP_UK" RENAME TO "NETWORK_IP_UK";

CREATE INDEX "PRSNLTY_SLI_PRSNLTY_IDX" ON personality_service_list_item (personality_id);

QUIT;
