
alter table host drop constraint host_lifecycle_fk;
drop table hostlifecycle;
rename hostlifecycle_id_seq to status_id_seq;

alter table host rename column lifecycle_id to status_id;
alter table host add constraint host_status_fk foreign key (status_id) references status(id);

alter table clstr drop constraint cluster_status_fk;
alter table clstr add constraint cluster_status_fk foreign key(status_id) references status(id);
alter table clstr modify status_id integer null;
alter table clstr drop column status_id;
drop table clusterlifecycle;
drop sequence clusterlifecycle_id_seq;

