-- this script add shares not added by upgrade_shares.sql
-- also rebinds virtual to these shares.

-- NOTE that this script is based on upgrade_shares.sql
-- and it fixes the disk - share - cluster relation based on the
-- disk - machine - cluster relation.

set serverout on
set autocommit off
DECLARE
	SH_COUNT INTEGER;
	SH_ID INTEGER;
	-- end-to-end select from service instance to vm holder.
	CURSOR svc_fetcher IS
		SELECT DISTINCT
            RES2.NAME as SHARE_NAME,
			RES2.COMMENTS AS SHARE_COMMENTS, RES2.CREATION_DATE AS SH_DATE,
			D.ID AS DISK_ID, D.DEVICE_NAME AS DISK_NAME,
			RES.HOLDER_ID AS HOLDER_ID,
			CLSTR.NAME AS CLUSTER_NAME,
            CLSTR.ID AS CLUSTER_ID
		FROM
            -- disk resource path
			"resource" RES2, RESHOLDER RH2, "share" SI, DISK D,
            -- vm resource path
			VIRTUAL_MACHINE, "resource" RES, RESHOLDER, CLSTR
		WHERE
            -- disk part -- wrong connection
            D.SHARE_ID = SI.ID AND
            RES2.ID = SI.ID AND
            RES2.HOLDER_ID = RH2.ID AND
            -- that means we didn't add the share to this cluster.
            RH2.CLUSTER_ID <> RESHOLDER.CLUSTER_ID AND
            -- machine part -- right connection
			D.MACHINE_ID = VIRTUAL_MACHINE.MACHINE_ID AND
			VIRTUAL_MACHINE.RESOURCE_ID = RES.ID AND
			RES.HOLDER_ID = RESHOLDER.ID AND
			RESHOLDER.CLUSTER_ID = CLSTR.ID
			order by SHARE_NAME, DISK_ID;

BEGIN
	-- create shares if for the given share.name, cluster.id we don't have it already
	FOR svc_rec IN svc_fetcher LOOP
        SELECT
            COUNT(*) INTO SH_COUNT
        FROM "share" SH, "resource" RES, RESHOLDER
        WHERE
            RES.NAME = svc_rec.SHARE_NAME AND
            SH.ID = RES.ID AND
            RES.HOLDER_ID = RESHOLDER.ID AND
            RESHOLDER.CLUSTER_ID = svc_rec.CLUSTER_ID;

		IF SH_COUNT = 0 THEN
			SH_ID := RESOURCE_SEQ.NEXTVAL;

			INSERT INTO "resource" (id, resource_type, name, creation_date, comments, holder_id)
				VALUES (SH_ID, 'share', svc_rec.SHARE_NAME, svc_rec.SH_DATE, svc_rec.SHARE_COMMENTS, svc_rec.HOLDER_ID);
			INSERT INTO "share" (id) VALUES (SH_ID);

			dbms_output.put_line('Create share ' || svc_rec.SHARE_NAME || ' for cluster ' || svc_rec.CLUSTER_NAME);
        ELSE
            SELECT
                 SH.ID INTO SH_ID
            FROM "share" SH, "resource" RES, RESHOLDER
            WHERE
                RES.NAME = svc_rec.SHARE_NAME AND
                SH.ID = RES.ID AND
                RES.HOLDER_ID = RESHOLDER.ID AND
                RESHOLDER.CLUSTER_ID = svc_rec.CLUSTER_ID;
		END IF;

		UPDATE DISK set share_id = SH_ID, DISK_TYPE = 'virtual_disk'
			WHERE DISK.ID = svc_rec.DISK_ID;

		dbms_output.put_line('Updated disk: ' || svc_rec.DISK_NAME || ' to share: ' || svc_rec.SHARE_NAME);
	END LOOP;
END;
/

commit;

QUIT;
