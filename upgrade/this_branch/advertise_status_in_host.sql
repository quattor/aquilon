ALTER TABLE host ADD advertise_status NUMBER(*,0);

UPDATE host SET advertise_status = 1 WHERE lifecycle_id IN (
		SELECT id FROM hostlifecycle WHERE name IN ('ready', 'reinstall', 'rebuild', 'failed', 'decommissioned'));

ALTER TABLE host ADD CONSTRAINT "CLSTR_DOWN_HOSTS_CK" CHECK (advertise_status IN (0, 1)) ENABLE;

COMMIT;
