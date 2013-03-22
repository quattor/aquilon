ALTER TABLE param_holder DROP CONSTRAINT param_holder_featurelink_fk;
ALTER TABLE param_holder DROP CONSTRAINT param_holder_flink_uk;
ALTER TABLE param_holder DROP COLUMN featurelink_id;
QUIT;
