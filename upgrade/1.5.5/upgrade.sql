alter table host drop constraint host_status_fk;

insert into status(id, name, creation_date) values(status_id_seq.nextval, 'decommissioned', sysdate);
insert into status(id, name, creation_date) values(status_id_seq.nextval, 'rebuild', sysdate);
insert into status(id, name, creation_date) values(status_id_seq.nextval, 'reinstall', sysdate);
rename status_id_seq to hostlifecycle_id_seq;

create table hostlifecycle (
        id integer not null, 
        name varchar(32) not null, 
        creation_date date not null, 
        comments varchar(255), 
        constraint hostlifecycle_pk primary key (id), 
        constraint hostlifecycle_uk unique (name)
);
insert into hostlifecycle select * from status;

alter table host rename column status_id to lifecycle_id;
alter table host add constraint host_lifecycle_fk foreign key (lifecycle_id) references hostlifecycle(id);

create table clusterlifecycle (
        id integer not null, 
        name varchar(32) not null, 
        creation_date date not null, 
        comments varchar(255), 
        constraint clusterlifecycle_pk primary key (id), 
        constraint clusterlifecycle_uk unique (name)
);
insert into clusterlifecycle select * from hostlifecycle where name in ('ready', 'build', 'decommissioned', 'rebuild');
create sequence clusterlifecycle_id_seq start with 50 increment by 1 nocache nocycle;
alter table clstr add status_id integer default(1) not null;
alter table clstr add constraint cluster_status_fk foreign key (status_id) references clusterlifecycle(id);


