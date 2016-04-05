ALTER TABLE clstr RENAME CONSTRAINT clstr_down_hosts_ck TO clstr_down_hosts_percent_ck;
ALTER TABLE clstr RENAME CONSTRAINT clstr_maint_hosts_ck TO clstr_down_maint_percent_ck;
ALTER TABLE host RENAME CONSTRAINT host_advertise_status_valid_ck TO host_advertise_status_ck;
ALTER TABLE xtn RENAME CONSTRAINT xtn_is_readonly TO xtn_is_readonly_ck;

QUIT;
