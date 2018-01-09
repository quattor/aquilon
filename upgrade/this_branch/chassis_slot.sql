ALTER TABLE chassis_slot ADD slot_type VARCHAR2(32);
UPDATE chassis_slot SET slot_type='machine';
ALTER TABLE chassis_slot MODIFY (slot_type CONSTRAINT chassis_slot_slot_type_nn NOT NULL);

ALTER TABLE chassis_slot ADD network_device_id NUMBER(38);

ALTER TABLE chassis_slot DROP CONSTRAINT CHASSIS_SLOT_PK CASCADE;
DROP index CHASSIS_SLOT_PK;
ALTER TABLE chassis_slot ADD CONSTRAINT CHASSIS_SLOT_PK PRIMARY KEY (chassis_id, slot_number, slot_type);

ALTER TABLE chassis_slot
ADD CONSTRAINT CHASSIS_SLOT_ASSIGN_CK
CHECK (
(CASE WHEN network_device_id IS NOT NULL THEN 1 ELSE 0 END
    + CASE WHEN machine_id IS NOT NULL THEN 1 ELSE 0 END)
    != 2
)

ALTER TABLE chassis_slot
ADD CONSTRAINT CHASSIS_SLOT_TYPE_MATCH_CK
CHECK (
(CASE WHEN slot_type='network_device' THEN 1 ELSE 0 END
    + CASE WHEN machine_id IS NOT NULL THEN 1 ELSE 0 END)
    != 2
AND
(CASE WHEN slot_type='machine' THEN 1 ELSE 0 END
    + CASE WHEN network_device_id IS NOT NULL THEN 1 ELSE 0 END)
    != 2
)

QUIT;
