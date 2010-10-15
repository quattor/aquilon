--- Migrate from tor_switch to switch

--- Rename tor_switch to switch
ALTER TABLE tor_switch RENAME TO switch;
---   Rename tor_switch_id to switch_id
ALTER TABLE switch RENAME COLUMN tor_switch_id TO switch_id;
---   Add switch_type, set to 'tor', make non-null
ALTER TABLE switch ADD (switch_type VARCHAR(16));
UPDATE switch SET switch_type = 'tor';
ALTER TABLE switch MODIFY (switch_type CONSTRAINT "SWITCH_SWITCH_TYPE_NN" NOT NULL ENABLE);
---   Fix the constraint names
ALTER TABLE switch RENAME CONSTRAINT "TOR_SW_ID_NN" TO "SWITCH_ID_NN";
ALTER TABLE switch RENAME CONSTRAINT "TOR_SW_TOR_SWITCH_ID_NN" TO "SWITCH_SWITCH_ID_NN";
ALTER TABLE switch RENAME CONSTRAINT "TOR_SWITCH_PK" TO "SWITCH_PK";
ALTER TABLE switch RENAME CONSTRAINT "TOR_SW_SYS_FK" TO "SWITCH_SYS_FK";
ALTER TABLE switch RENAME CONSTRAINT "TOR_SW_SY_HW_FK" TO "SWITCH_SYS_HW_FK";

--- Rename tor_switch_hw as switch_hw
ALTER TABLE tor_switch_hw RENAME TO switch_hw;
---   Fix the constraint names
ALTER TABLE switch_hw RENAME CONSTRAINT "TOR_SWITCH_HW_HW_ENT_ID_NN" TO "SWITCH_HW_HW_ENT_ID_NN";
ALTER TABLE switch_hw RENAME CONSTRAINT "TOR_SWITCH_HW_LAST_POLL_NN" TO "SWITCH_HW_LAST_POLL_NN";
ALTER TABLE switch_hw RENAME CONSTRAINT "TOR_SWITCH_HW_PK" TO "SWITCH_HW_PK";
ALTER TABLE switch_hw RENAME CONSTRAINT "TOR_SWITCH_HW_ENT_FK" TO "SWITCH_HW_ENT_FK";

--- Fix system_type in the system table
UPDATE system SET system_type = 'switch' WHERE system_type = 'tor_switch';

--- And hardware_entity_type in the HE table
UPDATE hardware_entity SET hardware_entity_type = 'switch_hw' WHERE hardware_entity_type = 'tor_switch_hw';

--- Fix model machine_type
UPDATE model SET machine_type = 'switch' WHERE machine_type = 'tor_switch';

--- Add model vendor=generic, name=temp_switch, type=switch
INSERT INTO model (id, name, vendor_id, machine_type, creation_date)
(SELECT MODEL_ID_SEQ.NEXTVAL, 'temp_switch', id, 'switch', SYSDATE
 FROM vendor
 WHERE name = 'generic');

COMMIT;
