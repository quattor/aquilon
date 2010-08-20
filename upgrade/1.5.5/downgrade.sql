
drop table hostlifecycle;
drop sequence hostlifecycle_id_seq;

rename hostlifecycle_id_seq to status_id_seq;

alter table "host" drop constraint "host_lifecycle_fk";
alter table "host" rename column lifecycle_id to status_id;
alter table "host" add constraint host_status_fk foreign key (status_id) references status(id);

alter table "esx_cluster" drop constraint "cluster_lifecycle_fk";
alter table "esx_cluster" add constraint "cluster_status_fk" foreign key(status_id) references status(id);
drop table clusterlifecycle;
drop sequence clusterlifecycle_id_seq;

