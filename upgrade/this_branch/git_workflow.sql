
ALTER TABLE "CLSTR" DROP CONSTRAINT "CLUSTER_DOMAIN_FK";
ALTER TABLE "HOST" DROP CONSTRAINT "HOST_DOMAIN_FK";

RENAME DOMAIN_ID_SEQ TO BRANCH_ID_SEQ;

CREATE TABLE branch (
        id INTEGER NOT NULL,
        branch_type VARCHAR(16) NOT NULL,
        name VARCHAR(32) NOT NULL,
        compiler VARCHAR(255) NOT NULL,
        is_sync_valid SMALLINT NOT NULL,
        autosync SMALLINT NOT NULL,
        owner_id INTEGER NOT NULL,
        creation_date DATE NOT NULL,
        comments VARCHAR(255),
        CONSTRAINT branch_pk PRIMARY KEY (id),
         CONSTRAINT branch_user_princ_fk FOREIGN KEY(owner_id) REFERENCES user_principal (id),
        CONSTRAINT branch_uk  UNIQUE (name)
);

-- Translate current domains into sandboxes.
INSERT INTO BRANCH (ID, BRANCH_TYPE, NAME, COMPILER, IS_SYNC_VALID, AUTOSYNC,
                    OWNER_ID, CREATION_DATE, COMMENTS)
(SELECT ID, 'sandbox', NAME, COMPILER, 1, 1, OWNER_ID, CREATION_DATE, COMMENTS
 FROM DOMAIN);

DROP TABLE DOMAIN;

CREATE TABLE domain (
        domain_id INTEGER NOT NULL,
        tracked_branch_id INTEGER,
        rollback_commit VARCHAR(40),
        CONSTRAINT domain_pk PRIMARY KEY (domain_id),
         CONSTRAINT domain_branch_fk FOREIGN KEY(tracked_branch_id) REFERENCES branch (id),
         CONSTRAINT domain_fk FOREIGN KEY(domain_id) REFERENCES branch (id) ON DELETE CASCADE
);


CREATE TABLE sandbox (
        sandbox_id INTEGER NOT NULL,
        CONSTRAINT sandbox_pk PRIMARY KEY (sandbox_id),
         CONSTRAINT sandbox_fk FOREIGN KEY(sandbox_id) REFERENCES branch (id) ON DELETE CASCADE
);


-- Create the production domain
INSERT INTO BRANCH (ID, BRANCH_TYPE, NAME, COMPILER, IS_SYNC_VALID, AUTOSYNC,
                    OWNER_ID, CREATION_DATE, COMMENTS)
(SELECT BRANCH_ID_SEQ.NEXTVAL, 'domain', 'prod',
        '/ms/dist/elfms/PROJ/panc/prod/lib/panc.jar', 1, 1, USER_PRINCIPAL.ID,
        SYSDATE, 'production domain'
 FROM USER_PRINCIPAL
 WHERE NAME = 'cdb');

-- Create the qa domain
INSERT INTO BRANCH (ID, BRANCH_TYPE, NAME, COMPILER, IS_SYNC_VALID, AUTOSYNC,
                    OWNER_ID, CREATION_DATE, COMMENTS)
(SELECT BRANCH_ID_SEQ.NEXTVAL, 'domain', 'qa',
        '/ms/dist/elfms/PROJ/panc/prod/lib/panc.jar', 1, 1, USER_PRINCIPAL.ID,
        SYSDATE, 'qa domain'
 FROM USER_PRINCIPAL
 WHERE NAME = 'cdb');

-- Finish creating the two domains
INSERT INTO DOMAIN (domain_id, tracked_branch_id, rollback_commit)
(SELECT ID, NULL, NULL FROM BRANCH WHERE NAME IN ('prod', 'qa'));

-- These two are not sandboxes, they are tracking domains...
UPDATE BRANCH SET BRANCH_TYPE='domain' WHERE NAME IN ('ny-prod', 'ny-qa');

-- Finish creating the tracking domains.
INSERT INTO DOMAIN (domain_id, tracked_branch_id, rollback_commit)
VALUES ((SELECT ID FROM BRANCH WHERE NAME='ny-prod'),
        (SELECT ID FROM BRANCH WHERE NAME='prod'),
        NULL);

INSERT INTO DOMAIN (domain_id, tracked_branch_id, rollback_commit)
VALUES ((SELECT ID FROM BRANCH WHERE NAME='ny-qa'),
        (SELECT ID FROM BRANCH WHERE NAME='qa'),
        NULL);

-- Finish creating the sandboxes.
INSERT INTO SANDBOX (SANDBOX_ID)
(SELECT ID FROM BRANCH WHERE BRANCH_TYPE = 'sandbox');

ALTER TABLE "CLSTR" RENAME COLUMN "DOMAIN_ID" TO "BRANCH_ID";
ALTER TABLE "CLSTR" ADD ("SANDBOX_AUTHOR_ID" INTEGER);
ALTER TABLE "CLSTR" ADD CONSTRAINT "CLUSTER_BRANCH_FK"
FOREIGN KEY("BRANCH_ID") REFERENCES "BRANCH" ("ID");
ALTER TABLE "CLSTR" ADD CONSTRAINT "CLUSTER_SANDBOX_AUTHOR_FK"
FOREIGN KEY("SANDBOX_AUTHOR_ID") REFERENCES "USER_PRINCIPAL" (ID);

UPDATE CLSTR SET SANDBOX_AUTHOR_ID = (SELECT ID FROM USER_PRINCIPAL
                                      WHERE NAME='cdb')
    WHERE EXISTS (SELECT 1 FROM BRANCH WHERE BRANCH_TYPE='sandbox'
                  AND BRANCH.ID = CLSTR.BRANCH_ID);

ALTER TABLE "HOST" RENAME COLUMN "DOMAIN_ID" TO "BRANCH_ID";
ALTER TABLE "HOST" ADD ("SANDBOX_AUTHOR_ID" INTEGER);
ALTER TABLE "HOST" ADD CONSTRAINT "HOST_BRANCH_FK"
FOREIGN KEY("BRANCH_ID") REFERENCES "BRANCH" ("ID");
ALTER TABLE "HOST" ADD CONSTRAINT "HOST_SANDBOX_AUTHOR_FK"
FOREIGN KEY("SANDBOX_AUTHOR_ID") REFERENCES "USER_PRINCIPAL" (ID);

UPDATE (SELECT HOST.SANDBOX_AUTHOR_ID AS AID, BRANCH.OWNER_ID AS OID
	FROM HOST, BRANCH
	WHERE HOST.BRANCH_ID = BRANCH.ID
	AND BRANCH.BRANCH_TYPE = 'sandbox') t
    SET AID = OID;

commit;
