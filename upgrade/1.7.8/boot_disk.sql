ALTER TABLE disk ADD bootable INTEGER;
UPDATE disk SET bootable = 1 WHERE device_name = 'sda' OR device_name = 'c0d0';
UPDATE disk SET bootable = 0 WHERE bootable IS NULL;
ALTER TABLE disk MODIFY (bootable INTEGER CONSTRAINT "DISK_BOOTABLE_NN" NOT NULL);
ALTER TABLE disk ADD CONSTRAINT "DISK_BOOTABLE_CK" CHECK (bootable IN (0, 1));

QUIT;
