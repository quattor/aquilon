ALTER SESSION ENABLE PARALLEL DML;

INSERT /*+ APPEND PARALLEL */ INTO xtn2_end SELECT xtn_end.* FROM xtn_end JOIN xtn2 ON xtn_end.xtn_id = xtn2.xtn_id;
COMMIT;

INSERT /*+ APPEND PARALLEL */ INTO xtn2_detail SELECT xtn_detail.* FROM xtn_detail JOIN xtn2 ON xtn_detail.xtn_id = xtn2.xtn_id;
COMMIT;

ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_pk;
ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_return_code_nn;
ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_end_time_nn;

ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_dtl_pk;
ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_detail_name_nn;
ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_detail_value_nn;

QUIT;
