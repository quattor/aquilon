ALTER SESSION FORCE PARALLEL DML;

CREATE TABLE xtn2 (
    id RAW(16) CONSTRAINT xtn2_id_nn NOT NULL DISABLE,
    username VARCHAR2(65 CHAR) CONSTRAINT xtn2_username_nn NOT NULL DISABLE,
    command VARCHAR2(64 CHAR) CONSTRAINT xtn2_command_nn NOT NULL DISABLE,
    is_readonly INTEGER CONSTRAINT xtn2_is_readonly_nn NOT NULL DISABLE,
    start_time DATE CONSTRAINT xtn2_start_time_nn NOT NULL DISABLE,
    CONSTRAINT xtn2_is_readonly_ck CHECK (is_readonly IN (0, 1)) DISABLE,
    CONSTRAINT xtn2_pk PRIMARY KEY (id) DISABLE
)
PARTITION BY RANGE (start_time)
(
   PARTITION xtn_2011_q2 VALUES LESS THAN (TO_DATE('01-07-2011', 'DD-MM-YYYY')),
   PARTITION xtn_2011_q3 VALUES LESS THAN (TO_DATE('01-10-2011', 'DD-MM-YYYY')),
   PARTITION xtn_2011_q4 VALUES LESS THAN (TO_DATE('01-01-2012', 'DD-MM-YYYY')),
   PARTITION xtn_2012_q1 VALUES LESS THAN (TO_DATE('01-04-2012', 'DD-MM-YYYY')),
   PARTITION xtn_2012_q2 VALUES LESS THAN (TO_DATE('01-07-2012', 'DD-MM-YYYY')),
   PARTITION xtn_2012_q3 VALUES LESS THAN (TO_DATE('01-10-2012', 'DD-MM-YYYY')),
   PARTITION xtn_2012_q4 VALUES LESS THAN (TO_DATE('01-01-2013', 'DD-MM-YYYY')),
   PARTITION xtn_2013_q1 VALUES LESS THAN (TO_DATE('01-04-2013', 'DD-MM-YYYY')),
   PARTITION xtn_2013_q2 VALUES LESS THAN (TO_DATE('01-07-2013', 'DD-MM-YYYY')),
   PARTITION xtn_2013_q3 VALUES LESS THAN (TO_DATE('01-10-2013', 'DD-MM-YYYY')),
   PARTITION xtn_2013_q4 VALUES LESS THAN (TO_DATE('01-01-2014', 'DD-MM-YYYY')),
   PARTITION xtn_2014_q1 VALUES LESS THAN (TO_DATE('01-04-2014', 'DD-MM-YYYY')),
   PARTITION xtn_2014_q2 VALUES LESS THAN (TO_DATE('01-07-2014', 'DD-MM-YYYY')),
   PARTITION xtn_2014_q3 VALUES LESS THAN (TO_DATE('01-10-2014', 'DD-MM-YYYY')),
   PARTITION xtn_2014_q4 VALUES LESS THAN (TO_DATE('01-01-2015', 'DD-MM-YYYY')),
   PARTITION xtn_2015_q1 VALUES LESS THAN (TO_DATE('01-04-2015', 'DD-MM-YYYY')),
   PARTITION xtn_2015_q2 VALUES LESS THAN (TO_DATE('01-07-2015', 'DD-MM-YYYY')),
   PARTITION xtn_2015_q3 VALUES LESS THAN (TO_DATE('01-10-2015', 'DD-MM-YYYY')),
   PARTITION xtn_2015_q4 VALUES LESS THAN (TO_DATE('01-01-2016', 'DD-MM-YYYY')),
   PARTITION xtn_2016_q1 VALUES LESS THAN (TO_DATE('01-04-2016', 'DD-MM-YYYY')),
   PARTITION xtn_2016_q2 VALUES LESS THAN (TO_DATE('01-07-2016', 'DD-MM-YYYY')),
   PARTITION xtn_2016_q3 VALUES LESS THAN (TO_DATE('01-10-2016', 'DD-MM-YYYY'))
) COMPRESS FOR OLTP PCTFREE 5;

INSERT /*+ APPEND PARALLEL */ INTO xtn2 (id, username, command, is_readonly, start_time)
	SELECT HEXTORAW(xtn.xtn_id), xtn.username, xtn.command, xtn.is_readonly, xtn.start_time
	FROM xtn;
COMMIT;

ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_id_nn;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_pk;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_username_nn;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_command_nn;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_is_readonly_nn;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_start_time_nn;
ALTER TABLE xtn2 ENABLE CONSTRAINT xtn2_is_readonly_ck;

EXECUTE dbms_stats.gather_table_stats(NULL, 'XTN2', degree => dbms_stats.auto_degree, granularity => 'ALL', cascade => TRUE);

CREATE TABLE xtn2_detail (
    xtn_id RAW(16) CONSTRAINT xtn2_detail_xtn_id_nn NOT NULL,
    name VARCHAR2(255 CHAR) CONSTRAINT xtn2_detail_name_nn NOT NULL DISABLE,
    value VARCHAR2(3000 CHAR) CONSTRAINT xtn2_detail_value_nn NOT NULL DISABLE,
    CONSTRAINT xtn2_detail_pk PRIMARY KEY (xtn_id, name, value) USING INDEX (CREATE UNIQUE INDEX xtn2_detail_pk ON xtn2_detail (xtn_id, name, value) LOCAL) DISABLE,
    CONSTRAINT xtn2_detail_xtn_fk FOREIGN KEY (xtn_id) REFERENCES xtn2 (id)
)
PARTITION BY REFERENCE (xtn2_detail_xtn_fk) COMPRESS FOR OLTP PCTFREE 5;

INSERT /*+ APPEND PARALLEL */ INTO xtn2_detail (xtn_id, name, value)
	SELECT HEXTORAW(xtn_detail.xtn_id), xtn_detail.name, xtn_detail.value
	FROM xtn_detail JOIN xtn2 ON xtn2.id = HEXTORAW(xtn_detail.xtn_id);
COMMIT;

ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_detail_pk;
ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_detail_name_nn;
ALTER TABLE xtn2_detail ENABLE CONSTRAINT xtn2_detail_value_nn;

EXECUTE dbms_stats.gather_table_stats(NULL, 'XTN2_DETAIL', degree => dbms_stats.auto_degree, granularity => 'ALL', cascade => TRUE);

CREATE TABLE xtn2_end (
    xtn_id RAW(16) CONSTRAINT xtn2_end_xtn_id_nn NOT NULL,
    return_code INTEGER CONSTRAINT xtn2_end_return_code_nn NOT NULL DISABLE,
    end_time DATE CONSTRAINT xtn2_end_end_time_nn NOT NULL DISABLE,
    CONSTRAINT xtn2_end_pk PRIMARY KEY (xtn_id) USING INDEX (CREATE UNIQUE INDEX xtn2_end_pk ON xtn2_end (xtn_id) LOCAL) DISABLE,
    CONSTRAINT xtn2_end_xtn_fk FOREIGN KEY (xtn_id) REFERENCES xtn2 (id)
)
PARTITION BY REFERENCE (xtn2_end_xtn_fk) COMPRESS FOR OLTP PCTFREE 5;

INSERT /*+ APPEND PARALLEL */ INTO xtn2_end (xtn_id, return_code, end_time)
	SELECT HEXTORAW(xtn_end.xtn_id), xtn_end.return_code, xtn_end.end_time
	FROM xtn_end JOIN xtn2 ON xtn2.id = HEXTORAW(xtn_end.xtn_id);
COMMIT;

ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_pk;
ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_return_code_nn;
ALTER TABLE xtn2_end ENABLE CONSTRAINT xtn2_end_end_time_nn;

EXECUTE dbms_stats.gather_table_stats(NULL, 'XTN2_END', degree => dbms_stats.auto_degree, granularity => 'ALL', cascade => TRUE);

QUIT;
