--------------------------------------
--  missed not null column definitions
--------------------------------------
ALTER TABLE ARCHETYPE MODIFY ("IS_COMPILEABLE" NOT NULL);

-----------------
-- CONSTRAINTS --
-----------------
ALTER TABLE "MODEL" DROP CONSTRAINT "SYS_C0046434";
DROP INDEX "IX_MODEL_NAME";

ALTER TABLE "MODEL" ADD CONSTRAINT "MODEL_VENDOR_NAME_UK" UNIQUE (
    "NAME", "VENDOR_ID") ENABLE;

----------------
-- TABLES
----------------
--can this be a case statement for count(*) of column == 0?
--DROP TABLE "CONSOLE_SERVER" CASCADE CONSTRAINTS;
--DROP TABLE "CONSOLE_SERVER_HW" CASCADE CONSTRAINTS;
--DROP TABLE "SERIAL_CNXN" CASCADE CONSTRAINTS;
--DROP TABLE "LOCATION_SEARCH_LIST" CASCADE CONSTRAINTS;
--DROP TABLE "SEARCH_LIST_ITEM" CASCADE CONSTRAINTS;

----------------
-- COLUMNS
----------------
--can this be a case statement for count(*) of column == 0?
ALTER TABLE "MACHINE" DROP COLUMN "SERIAL_NO";


---------------
--- Indexes ---
---------------

--ALTER INDEX "system_PT_uk" RENAME TO SYSTEM_PT_UK;
