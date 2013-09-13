-- DISK

ALTER TABLE disk ADD snapshotable NUMBER(*,0);
-- UPDATE disk SET snapshotable = 0;

ALTER TABLE disk ADD CONSTRAINT disk_snapshotable_ck CHECK (snapshotable IN (0, 1)) ENABLE;
-- ALTER TABLE DISK MODIFY (snapshotable NUMBER(*,0) CONSTRAINT disk_snapshotable_nn NOT NULL);


QUIT;
