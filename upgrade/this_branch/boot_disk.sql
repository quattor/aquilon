ALTER TABLE disk ADD bootable INTEGER DEFAULT 0;
UPDATE disk SET bootable = 1 WHERE device_name = 'sda' OR device_name = 'c0d0';
ALTER TABLE disk MODIFY (bootable INTEGER CONSTRAINT "DISK_BOOTABLE_NN" NOT NULL);
ALTER TABLE disk ADD CONSTRAINT "DISK_BOOTABLE_CK" CHECK (bootable in (0, 1));

QUIT;
