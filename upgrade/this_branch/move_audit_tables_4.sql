CREATE INDEX xtn_start_time_idx ON xtn (start_time DESC) LOCAL;
CREATE INDEX xtn_command_idx ON xtn (command) COMPRESS LOCAL;
CREATE INDEX xtn_username_idx ON xtn (username) COMPRESS LOCAL;
CREATE BITMAP INDEX xtn_isreadonly_idx ON xtn (is_readonly ASC) LOCAL;
CREATE INDEX xtn_dtl_value_idx ON xtn_detail (value) COMPRESS LOCAL;
CREATE INDEX xtn_dtl_name_idx ON xtn_detail (name) COMPRESS LOCAL;
CREATE INDEX xtn_end_return_code_idx ON xtn_end (return_code) COMPRESS LOCAL;

ALTER TABLE xtn RENAME CONSTRAINT xtn2_xtn_id_nn TO xtn_xtn_id_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_command_nn TO xtn_command_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_is_readonly_nn TO xtn_is_readonly_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_start_time_nn TO xtn_start_time_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_username_nn TO xtn_username_nn;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_is_readonly TO xtn_is_readonly;
ALTER TABLE xtn RENAME CONSTRAINT xtn2_pk TO xtn_pk;

ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_xtn_id_nn TO xtn_detail_xtn_id_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_name_nn TO xtn_detail_name_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_detail_value_nn TO xtn_detail_value_nn;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_dtl_pk TO xtn_dtl_pk;
ALTER TABLE xtn_detail RENAME CONSTRAINT xtn2_dtl_xtn_fk TO xtn_dtl_xtn_fk;

ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_xtn_id_nn TO xtn_end_xtn_id_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_end_time_nn TO xtn_end_end_time_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_return_code_nn TO xtn_end_return_code_nn;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_pk TO xtn_end_pk;
ALTER TABLE xtn_end RENAME CONSTRAINT xtn2_end_xtn_fk TO xtn_end_xtn_fk;

ALTER INDEX xtn2_pk RENAME TO xtn_pk;
ALTER INDEX xtn2_dtl_pk RENAME TO xtn_dtl_pk;
ALTER INDEX xtn2_end_pk RENAME TO xtn_end_pk;

QUIT;
