ALTER TABLE build_item DROP PRIMARY KEY DROP INDEX;
ALTER TABLE build_item DROP CONSTRAINT build_item_uk;
DROP INDEX build_item_uk;
ALTER TABLE build_item DROP COLUMN id;
ALTER TABLE build_item DROP COLUMN creation_date;
ALTER TABLE build_item DROP COLUMN comments;
ALTER TABLE build_item ADD CONSTRAINT build_item_pk PRIMARY KEY (host_id, service_instance_id);

ALTER TABLE host_cluster_member DROP COLUMN creation_date;

ALTER TABLE clstr_allow_per DROP COLUMN creation_date;

ALTER TABLE cluster_service_binding DROP COLUMN creation_date;
ALTER TABLE cluster_service_binding DROP COLUMN comments;

ALTER TABLE service_list_item DROP PRIMARY KEY DROP INDEX;
ALTER TABLE service_list_item DROP CONSTRAINT svc_list_svc_uk;
DROP INDEX svc_list_svc_uk;
ALTER TABLE service_list_item DROP COLUMN id;
ALTER TABLE service_list_item DROP COLUMN creation_date;
ALTER TABLE service_list_item DROP COLUMN comments;
ALTER TABLE service_list_item ADD CONSTRAINT service_list_item_pk PRIMARY KEY (service_id, archetype_id);

ALTER TABLE personality_service_list_item DROP COLUMN creation_date;
ALTER TABLE personality_service_list_item DROP COLUMN comments;

QUIT;
