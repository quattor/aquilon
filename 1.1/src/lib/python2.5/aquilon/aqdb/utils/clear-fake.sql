delete from host where comments like '%FAKE%';
delete from machine where comments like '%FAKE%' or name like '%FAKE';
delete from rack where id in (select id from location where comments like '%FAKE%');
delete from chassis where id in (select id from location where comments like '%FAKE%');
delete from location where comments like '%FAKE%';

