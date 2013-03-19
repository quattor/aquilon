
-- lookup all clusters the have vm's with nas disks
-- NOT: they're already there for the VMs. Create resholder record for these clusters if needed.

set serverout on
set autocommit off
DECLARE
	SH_ID INTEGER;
	CURRENT_SH_NAME VARCHAR2(64);
	-- end-to-end select from service instance to vm holder.
	CURSOR svc_fetcher IS
		SELECT DISTINCT
			SI.ID as SH_ID, SI.NAME as SHARE_NAME,
			SI.COMMENTS AS SHARE_COMMENTS, SI.CREATION_DATE AS SH_DATE,
			D.ID AS DISK_ID, D.DEVICE_NAME AS DISK_NAME,
			RES.HOLDER_ID AS HOLDER_ID,
			CLSTR.NAME AS CLUSTER_NAME
		FROM
			SERVICE SVC, SERVICE_INSTANCE SI, DISK D,
			VIRTUAL_MACHINE, "resource" RES, RESHOLDER, CLSTR
		WHERE
			SVC.NAME = 'nas_disk_share' AND
			SI.SERVICE_ID = SVC.ID AND
			D.SERVICE_INSTANCE_ID = SI.ID AND
			D.MACHINE_ID = VIRTUAL_MACHINE.MACHINE_ID AND
			VIRTUAL_MACHINE.RESOURCE_ID = RES.ID AND
			RES.HOLDER_ID = RESHOLDER.ID AND
			RESHOLDER.CLUSTER_ID = CLSTR.ID
			order by SH_ID, DISK_ID;
BEGIN
	CURRENT_SH_NAME := 'doesnt-exist'; -- emtpy string is NULL, the <> would result in NULL

	-- create shares for each nas service instance
	FOR svc_rec IN svc_fetcher LOOP
		IF CURRENT_SH_NAME <> svc_rec.SHARE_NAME THEN
			SH_ID := RESOURCE_SEQ.NEXTVAL;

			INSERT INTO "resource" (id, resource_type, name, creation_date, comments, holder_id)
				VALUES (SH_ID, 'share', svc_rec.SHARE_NAME, svc_rec.SH_DATE, svc_rec.SHARE_COMMENTS, svc_rec.HOLDER_ID);
			INSERT INTO "share" (id, latency) VALUES (SH_ID, NULL);

			CURRENT_SH_NAME := svc_rec.SHARE_NAME;
			dbms_output.put_line('Create share ' || svc_rec.SHARE_NAME || ' for cluster ' || svc_rec.CLUSTER_NAME);
		END IF;

		UPDATE DISK set share_id = SH_ID, DISK_TYPE = 'virtual_disk'
			WHERE DISK.ID = svc_rec.DISK_ID;

		dbms_output.put_line('Updated disk: ' || svc_rec.DISK_NAME || ' to share: ' || svc_rec.SHARE_NAME);
	END LOOP;
END;
/

commit;

---- post update schema changes
UPDATE MACHINE_SPECS SET DISK_TYPE = 'virtual_disk' WHERE DISK_TYPE = 'nas';

ALTER TABLE DISK DROP CONSTRAINT NAS_DISK_SRV_INST_FK;
ALTER TABLE DISK DROP COLUMN SERVICE_INSTANCE_ID;

DELETE FROM SERVICE_INSTANCE WHERE SERVICE_ID in (SELECT ID FROM SERVICE WHERE NAME = 'nas_disk_share');
ALTER TABLE SERVICE_INSTANCE DROP COLUMN MANAGER;

ALTER TABLE "share" DROP COLUMN LATENCY;

QUIT;
