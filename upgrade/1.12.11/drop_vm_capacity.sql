ALTER TABLE esx_cluster DROP COLUMN memory_capacity;
DROP TABLE personality_esx_cluster_info;
DROP TABLE personality_cluster_info;
DROP SEQUENCE pers_clstr_id_seq;

QUIT;
