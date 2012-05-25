-- CLSTR

ALTER TABLE CLSTR DROP CONSTRAINT CLSTR_DOWN_HOSTS_PERCENT_NN;
ALTER TABLE CLSTR DROP CONSTRAINT CLSTR_DOWN_HOSTS_THR_NN;
ALTER TABLE CLSTR DROP CONSTRAINT CLSTR_DOWN_MAINT_PERCENT_NN;


-- RESOURCEGROUP

ALTER TABLE RESOURCEGROUP ADD REQUIRED_TYPE VARCHAR2(32);


-- SHARE
-- lowercase since share is reserved oracle keyword, see resource.sql for the same trick
CREATE TABLE "share" (
    "ID" INTEGER CONSTRAINT "share_ID_NN" NOT NULL ENABLE,
    "LATENCY" INTEGER,
    CONSTRAINT "share_PK" PRIMARY KEY ("ID") ENABLE,
    CONSTRAINT "share_RESOURCE_FK" FOREIGN KEY ("ID") REFERENCES "resource" ("ID") ON DELETE CASCADE ENABLE
);


-- DISK

ALTER TABLE DISK ADD SHARE_ID INTEGER;
ALTER TABLE DISK ADD CONSTRAINT DISK_SHARE_FK FOREIGN KEY (SHARE_ID) REFERENCES "share" (ID) ON DELETE CASCADE;


-- METACLUSTER

-- remove existing, unneeded constraints
ALTER TABLE METACLUSTER DROP CONSTRAINT METACLUSTER_UK;
DROP SEQUENCE METACLUSTER_SEQ;

--    create a temporary CLUSTER_ID field in METACLUSTER
ALTER TABLE METACLUSTER ADD CLUSTER_ID INTEGER;

ALTER TABLE METACLUSTER_MEMBER DISABLE CONSTRAINT METACLUSTER_MEMBER_META_FK;
ALTER TABLE METACLUSTER_MEMBER DISABLE CONSTRAINT METACLUSTER_MEMBER_PK;

DECLARE
    cl_id INTEGER;
    loc_id INTEGER;
    arch_id INTEGER;

    pers_id INTEGER;
    branch_id INTEGER;
    status_id INTEGER;

BEGIN
    select id into loc_id from location where location_type = 'company' and name = 'ms';
    select id into status_id from clusterlifecycle where name = 'ready';
    select id into branch_id from branch where branch_type = 'domain' and name = 'ny-prod';

    -- metacluster archetype
    arch_id := ARCHETYPE_ID_SEQ.NEXTVAL;

    INSERT INTO ARCHETYPE(id, name, outputdesc, is_compileable, cluster_type, creation_date)
        VALUES(arch_id, 'metacluster', 'Meta', 1, 'meta', sysdate);

    -- metacluster personality
    pers_id := prsnlty_SEQ.NEXTVAL;

    INSERT INTO PERSONALITY(id, name, archetype_id, cluster_required, creation_date)
        VALUES(pers_id, 'metacluster', arch_id, 0, sysdate);

    -- migrate data from metacluster to clstr
    FOR mc_rec IN (SELECT ID, COMMENTS, CREATION_DATE, NAME FROM METACLUSTER) LOOP

        CL_ID := CLSTR_SEQ.NEXTVAL;

        -- create new CLUSTER records for every METACLUSTER
        INSERT INTO CLSTR(id, name, cluster_type, personality_id, branch_id, location_constraint_id, creation_date, status_id, comments)
            VALUES(CL_ID, mc_rec.NAME, 'meta', pers_id, branch_id, loc_id, mc_rec.CREATION_DATE, status_id, mc_rec.COMMENTS);

        -- add CLUSTER record ID to METACLUSTER
        UPDATE METACLUSTER SET CLUSTER_ID = CL_ID
        WHERE ID = mc_rec.ID;

        -- update METACLUSTER_MEMBER reference based on CLUSTER_ID
        UPDATE METACLUSTER_MEMBER SET METACLUSTER_ID = CL_ID
        WHERE METACLUSTER_ID = mc_rec.ID;

    END LOOP;

    -- update METACLUSTER ID based on CLUSTER_ID
    FOR mc_rec IN (SELECT ID, CLUSTER_ID FROM METACLUSTER) LOOP

        UPDATE METACLUSTER SET ID = mc_rec.CLUSTER_ID
        WHERE ID = mc_rec.ID;

    END LOOP;

END;
/

ALTER TABLE METACLUSTER_MEMBER ENABLE CONSTRAINT METACLUSTER_MEMBER_META_FK;
ALTER TABLE METACLUSTER_MEMBER ENABLE CONSTRAINT METACLUSTER_MEMBER_PK;

--    drop temporary CLUSTER_ID field in METACLUSTER
ALTER TABLE METACLUSTER DROP COLUMN CLUSTER_ID;
-- END

ALTER TABLE METACLUSTER DROP COLUMN COMMENTS;
ALTER TABLE METACLUSTER DROP COLUMN CREATION_DATE;
ALTER TABLE METACLUSTER DROP COLUMN NAME;

ALTER TABLE METACLUSTER ADD CONSTRAINT META_CLUSTER_FK FOREIGN KEY (ID) REFERENCES CLSTR (ID) ON DELETE CASCADE;

QUIT;
