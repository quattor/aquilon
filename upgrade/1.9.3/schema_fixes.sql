ALTER TABLE parameter MODIFY (holder_id CONSTRAINT parameter_holder_id_nn NOT NULL);
ALTER TABLE param_definition MODIFY (holder_id CONSTRAINT param_definition_holder_id_nn NOT NULL);
