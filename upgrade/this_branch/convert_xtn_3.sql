ALTER SESSION FORCE PARALLEL DML;

CREATE INDEX xtn_start_time_idx ON xtn (start_time DESC) LOCAL;
CREATE BITMAP INDEX xtn_command_idx ON xtn (command) LOCAL;
CREATE INDEX xtn_username_idx ON xtn (username) COMPRESS LOCAL;
CREATE BITMAP INDEX xtn_is_readonly_idx ON xtn (is_readonly ASC) LOCAL;
CREATE INDEX xtn_detail_value_idx ON xtn_detail (value) COMPRESS LOCAL;
CREATE INDEX xtn_detail_name_idx ON xtn_detail (name) COMPRESS LOCAL;
CREATE INDEX xtn_end_return_code_idx ON xtn_end (return_code) COMPRESS LOCAL;

QUIT;
