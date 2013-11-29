ALTER TABLE model RENAME COLUMN machine_type TO model_type;
ALTER TABLE model RENAME CONSTRAINT model_machine_type_nn TO model_model_type_nn;
ALTER TABLE model MODIFY (model_type VARCHAR2(20));

QUIT;
