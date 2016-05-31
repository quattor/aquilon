DROP TABLE xtn_end;
RENAME xtn2_end TO xtn_end;

ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_xtn_id_nn TO xtn_end_xtn_id_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_end_time_nn TO xtn_end_end_time_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_return_code_nn TO xtn_end_return_code_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_pk TO xtn_end_pk;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_xtn_fk TO xtn_end_xtn_fk;

DROP TABLE xtn_detail;
RENAME xtn2_detail TO xtn_detail;

ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_xtn_id_nn TO xtn_detail_xtn_id_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_name_nn TO xtn_detail_name_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_value_nn TO xtn_detail_value_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_pk TO xtn_detail_pk;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_xtn_fk TO xtn_detail_xtn_fk;

DROP TABLE xtn;
RENAME xtn2 TO xtn;

ALTER TABLE xtn RENAME CONSTRAINT xtn2_id_nn TO xtn_id_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_command_nn TO xtn_command_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_is_readonly_nn TO xtn_is_readonly_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_start_time_nn TO xtn_start_time_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_username_nn TO xtn_username_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_is_readonly_ck TO xtn_is_readonly_ck;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_pk TO xtn_pk;

ALTER INDEX xtn2_pk RENAME TO xtn_pk;
ALTER INDEX xtn2_detail_pk RENAME TO xtn_detail_pk;
ALTER INDEX xtn2_end_pk RENAME TO xtn_end_pk;

QUIT;
