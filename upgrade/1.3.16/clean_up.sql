drop table temp_personality;
drop table temp_host_info;
drop table old_host;
commit;


begin 
    DBMS_STATS.GATHER_SCHEMA_STATS (
        ownname => 'cdb',
        --options=>'GATHER EMPTY',
        --method_opt=>'for all columns size repeat',
        cascade => TRUE,
        estimate_percent => 100);
end;


exit;
