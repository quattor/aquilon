--create a temp table as a copy of the data we need
create table temp_personality as select * from cfg_path
where tld_id = (select id from tld where type='personality');

CREATE TABLE PERSONALITY(
  ID NUMBER(38,0) CONSTRAINT PERSONALITY_ID_NN NOT NULL ENABLE,
  NAME VARCHAR2(32 BYTE) CONSTRAINT PERSONALITY_NAME_NN NOT NULL ENABLE,
  ARCHETYPE_ID NUMBER(38,0) CONSTRAINT PERSONALITY_ARCHETYPE_ID_NN NOT NULL ENABLE,
  CREATION_DATE DATE CONSTRAINT PERSONALITY_CR_DATE_NN NOT NULL ENABLE,
  COMMENTS VARCHAR2(255),
  CONSTRAINT PRSNLTY_PK PRIMARY KEY (ID) ENABLE, 
  CONSTRAINT PERSONALITY_UK UNIQUE (NAME, ARCHETYPE_ID) ENABLE,
  CONSTRAINT PRSNLTY_ARCH_FK FOREIGN KEY (ARCHETYPE_ID) REFERENCES ARCHETYPE (ID) ENABLE
);
commit;

CREATE SEQUENCE PERSONALITY_SEQ;
commit;

insert into personality(id, archetype_id, name, creation_date, comments)
  select (personality_seq.nextval) as ID,
  (select id from archetype where name='aquilon') AS ARCHETYPE_ID,
  relative_path as NAME,
  creation_date,
  comments
from cfg_path where tld_id = (select id from tld where type='personality');
commit;

--Create generic personalities for non-build archtypes
insert into personality (id, archetype_id, name, creation_date)
    select personality_seq.nextval, id as ARCHETYPE_ID, 'generic', sysdate from archetype
        where id not in (select distinct archetype_id from personality);
commit;

--Visualize the results
--select B.name as ARCHETYPE, A.name as PERSONALITY from personality A, archetype B where A.ARCHETYPE_ID = B.ID;

--we have usable personalities for every archetype, update the host table.

/* *** HOST TABLE UPGRADE *** */


/*--Create a temporary table with host_id, archetype_id, personality name (nullable), personality_id */
CREATE TABLE temp_host_info as
select A.id as host_id, A.archetype_id, C.RELATIVE_PATH AS personality, D.ID as personality_id
from host A, build_item B, cfg_path C, personality D
where A.id = B.HOST_ID
AND B.CFG_PATH_ID = C.ID
AND C.TLD_ID = (select id from tld where type = 'personality')
AND D.name = C.relative_path;
commit;

create table old_host as select * from host;
commit;

--Add personality_id column and populate
ALTER TABLE HOST ADD (PERSONALITY_ID NUMBER(*,0));
commit;

/* This is a long winded way of updating the one windows host to have the right personality  */
UPDATE host SET personality_id =(
    select id from personality where archetype_id = (
        select id from archetype where name = 'windows'))
WHERE personality_id is NULL
AND archetype_id =(select id from archetype where name = 'windows');
commit;

UPDATE host SET personality_id =(
    select id from personality where archetype_id = (
        select id from archetype where name = 'aurora'))
WHERE personality_id is NULL
AND archetype_id =(select id from archetype where name = 'aurora');
commit;

UPDATE HOST SET (personality_id) = (
    select personality_id from temp_host_info  where host_id = id)
WHERE personality_id is NULL
AND archetype_id = (
   select id from archetype where name = 'aquilon');
commit;


UPDATE HOST SET personality_id = (
    select id from personality where name = 'inventory') 
WHERE personality_id IS NULL
AND archetype_id = (
    select id from archetype where name = 'aquilon');
commit;


--Drop archetype_id column
ALTER TABLE HOST DROP CONSTRAINT HOST_ARCHETYPE_ID_NN;
ALTER TABLE HOST DROP CONSTRAINT HOST_ARCH_FK;
ALTER TABLE HOST DROP COLUMN ARCHETYPE_ID;
commit;

ALTER TABLE HOST add constraint HOST_PRSNLTY_ID_NN check(PERSONALITY_ID IS NOT NULL) ENABLE;
ALTER TABLE HOST ADD CONSTRAINT HOST_PRSNLTY_FK FOREIGN KEY (PERSONALITY_ID) REFERENCES PERSONALITY (ID) ENABLE;
commit;

CREATE INDEX HOST_PRSNLTY_IDX ON HOST (PERSONALITY_ID);
CREATE INDEX PRSNLTY_ARCH_IDX ON PERSONALITY (ARCHETYPE_ID);

--Remove all personality cfg_path/personality build_items from the build_item table (put them in a temp_table first)
DELETE FROM BUILD_ITEM WHERE CFG_PATH_ID IN (SELECT ID FROM TEMP_PERSONALITY);
commit;

--Remove all the cfg_paths of type personality (put them in a temp_table first)
DELETE FROM CFG_PATH WHERE ID IN (SELECT ID FROM CFG_PATH where tld_id = (select id from tld where type = 'personality'));
commit;

DELETE FROM TLD WHERE type='personality';
commit;

ANALYZE TABLE archetype COMPUTE STATISTICS;
ANALYZE TABLE personality COMPUTE STATISTICS;
ANALYZE TABLE host COMPUTE STATISTICS;
ANALYZE TABLE build_item COMPUTE STATISTICS;
ANALYZE TABLE system COMPUTE STATISTICS;

CREATE TABLE PERSONALITY_SERVICE_MAP (	
  ID NUMBER(*,0) CONSTRAINT PRSNLTY_SVC_MAP_ID_NN NOT NULL ENABLE, 
  SERVICE_INSTANCE_ID NUMBER(*,0) CONSTRAINT PRSNLTY_SVC_MAP_SVC_INST_NN NOT NULL ENABLE, 
  LOCATION_ID NUMBER(*,0) CONSTRAINT PRSNLTY_SVC_MAP_LOC_ID_NN NOT NULL ENABLE, 
  PERSONALITY_ID NUMBER(*,0) CONSTRAINT PRSNLTY_SVC_MAP_PRSNLTY_ID_NN NOT NULL ENABLE, 
  CREATION_DATE DATE CONSTRAINT PRSNLTY_SVC_MAP_CR_DATE_NN NOT NULL ENABLE, 
  COMMENTS VARCHAR2(255 BYTE),	 
  CONSTRAINT PRSNLTY_SVC_MAP_PK PRIMARY KEY (ID) ENABLE,
  CONSTRAINT PRSNLTY_SVC_MAP_LOC_INST_UK UNIQUE (PERSONALITY_ID, SERVICE_INSTANCE_ID, LOCATION_ID) ENABLE,
  CONSTRAINT PRSNLTY_SVC_MAP_SVC_INST_FK FOREIGN KEY (SERVICE_INSTANCE_ID) REFERENCES SERVICE_INSTANCE (ID) ENABLE,  
  CONSTRAINT PERSONALITY FOREIGN KEY (PERSONALITY_ID) REFERENCES PERSONALITY (ID) ON DELETE CASCADE ENABLE, 
  CONSTRAINT PRSNLTY_SVC_MAP_LOC_FK FOREIGN KEY (LOCATION_ID) REFERENCES LOCATION (ID) ON DELETE CASCADE ENABLE
);
commit; 

CREATE SEQUENCE PRSNLTY_SVC_MAP_SEQ;
commit;

CREATE TABLE PERSONALITY_SERVICE_LIST_ITEM(
  SERVICE_ID NUMBER(*,0) CONSTRAINT PRSNLTY_SLI_SERVICE_ID_NN NOT NULL ENABLE, 
	PERSONALITY_ID NUMBER(*,0) CONSTRAINT PRSNLTY_SLI_PERSONALITY_ID_NN NOT NULL ENABLE, 
	CREATION_DATE DATE CONSTRAINT PRSNLTY_SLI_CR_DATE_NN NOT NULL ENABLE, 
	COMMENTS VARCHAR2(255 BYTE), 
  CONSTRAINT PRSNLTY_SLI_PK PRIMARY KEY (SERVICE_ID, PERSONALITY_ID) ENABLE, 
  CONSTRAINT SLI_PRSNLTY_FK FOREIGN KEY (PERSONALITY_ID) REFERENCES PERSONALITY (ID) ON DELETE CASCADE ENABLE, 
  CONSTRAINT PRSNLTY_SLI_SVC_FK FOREIGN KEY (SERVICE_ID) REFERENCES SERVICE (ID) ON DELETE CASCADE ENABLE
);

/* no sequence needed for this guy: using the natural primary key */

exit;
