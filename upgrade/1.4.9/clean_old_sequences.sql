--drop old / unused sequences:

drop sequence DISK_TYPE_SEQ;
drop sequence TLD_SEQ;
drop sequence CFG_PATH_ID_SEQ;
drop sequence LOCATION_SEARCH_LIST_ID_SEQ;
drop sequence SLI_SEQ;

--clean up old junk:
PURGE RECYCLEBIN;

commit;
