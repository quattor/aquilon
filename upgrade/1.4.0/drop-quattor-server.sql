ALTER TABLE "DOMAIN" DROP COLUMN "SERVER_ID";
commit;

DROP TABLE "QUATTOR_SERVER" CASCADE CONSTRAINTS;
commit;

DELETE FROM system WHERE system_type = 'quattor_server';
commit;
