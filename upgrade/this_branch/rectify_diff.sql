--------------------------------------
--  missed not null column definitions
--------------------------------------
ALTER TABLE ARCHETYPE MODIFY ("IS_COMPILEABLE" NOT NULL);

-----------------
-- CONSTRAINTS --
-----------------
--only needs to be done against prod db
ALTER TABLE "MODEL" DROP CONSTRAINT "SYS_C0046434";
DROP INDEX "IX_MODEL_NAME";

ALTER TABLE "MODEL" ADD CONSTRAINT "MODEL_VENDOR_NAME_UK" UNIQUE (
    "NAME", "VENDOR_ID") ENABLE;

----------------
-- TABLES
----------------
--can this be a case statement for count(*) of table == 0?
DROP TABLE "CONSOLE_SERVER" CASCADE CONSTRAINTS;
DROP TABLE "CONSOLE_SERVER_HW" CASCADE CONSTRAINTS;
DROP TABLE "LOCATION_SEARCH_LIST" CASCADE CONSTRAINTS;
DROP TABLE "SEARCH_LIST_ITEM" CASCADE CONSTRAINTS;

----------------
-- COLUMNS
----------------
--can this be a case statement for count(*) of column is not null == 0?
ALTER TABLE "MACHINE" DROP COLUMN "SERIAL_NO";

---------------
--- Indexes ---
---------------
ALTER INDEX "system_PT_uk" RENAME TO "SYSTEM_PT_UK";

---------------
---  Data   ---
---------------
DELETE FROM user_principal WHERE name = 'kovacsk';
commit;

