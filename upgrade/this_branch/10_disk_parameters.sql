ALTER TABLE disk ADD disk_tech VARCHAR(32) DEFAULT NULL;
ALTER TABLE disk ADD diskgroup_key VARCHAR(255) DEFAULT NULL;
ALTER TABLE disk ADD model_key VARCHAR(255) DEFAULT NULL;
ALTER TABLE disk ADD usage VARCHAR(32) DEFAULT NULL;
ALTER TABLE disk ADD vsan_policy_key VARCHAR(255) DEFAULT NULL;
QUIT;
