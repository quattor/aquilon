set colsep ,     
set pagesize 0   
set trimspool on 
set headsep off  
set linesize 1000
--set numw X       

SELECT DISTINCT
    RES2.NAME || ', ' || D.DEVICE_NAME || ', ' || HW.LABEL || ', ' || CLSTR.NAME || '#',
    RES2.NAME, CLSTR.NAME
    -- RES2.NAME as SHARE_NAME,
    -- RES2.COMMENTS AS SHARE_COMMENTS, RES2.CREATION_DATE AS SH_DATE,
    -- D.ID AS DISK_ID, D.DEVICE_NAME AS DISK_NAME,
    -- RES.HOLDER_ID AS HOLDER_ID,
    -- CLSTR.NAME AS CLUSTER_NAME,
    -- CLSTR.ID AS CLUSTER_ID
FROM
    -- disk resource path
    "resource" RES2, RESHOLDER RH2, "share" SI, DISK D,
    HARDWARE_ENTITY HW,
    -- vm resource path
    VIRTUAL_MACHINE, "resource" RES, RESHOLDER, CLSTR
WHERE
    -- disk part
    D.SHARE_ID = SI.ID AND
    RES2.ID = SI.ID AND
    RES2.HOLDER_ID = RH2.ID AND
    -- machine part
    D.MACHINE_ID = VIRTUAL_MACHINE.MACHINE_ID AND
    VIRTUAL_MACHINE.RESOURCE_ID = RES.ID AND
    VIRTUAL_MACHINE.MACHINE_ID = HW.ID AND
    RES.HOLDER_ID = RESHOLDER.ID AND
    RESHOLDER.CLUSTER_ID = CLSTR.ID
    order by RES2.NAME, CLSTR.NAME;
EXIT;
