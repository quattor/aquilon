ALTER TABLE machine ADD (cpu_model_id INTEGER);
ALTER TABLE machine_specs ADD (cpu_model_id INTEGER);
ALTER TABLE cpu ADD (model_id INTEGER);

UPDATE cpu SET model_id = model_id_seq.NEXTVAL;
INSERT INTO model (id, name, vendor_id, model_type, comments, creation_date)
	SELECT model_id, name, vendor_id, 'cpu', comments, creation_date FROM cpu;
UPDATE machine SET cpu_model_id = (SELECT model_id FROM cpu WHERE machine.cpu_id = cpu.id);
UPDATE machine_specs SET cpu_model_id = (SELECT model_id FROM cpu WHERE machine_specs.cpu_id = cpu.id);

ALTER TABLE machine DROP CONSTRAINT machine_cpu_fk;
ALTER TABLE machine DROP COLUMN cpu_id;
ALTER TABLE machine ADD CONSTRAINT machine_cpu_model_fk FOREIGN KEY (cpu_model_id) REFERENCES model (id);
ALTER TABLE machine MODIFY (cpu_model_id CONSTRAINT machine_cpu_model_id_nn NOT NULL);

ALTER TABLE machine_specs DROP CONSTRAINT machine_specs_cpu_fk;
ALTER TABLE machine_specs DROP COLUMN cpu_id;
ALTER TABLE machine_specs ADD CONSTRAINT machine_specs_cpu_model_fk FOREIGN KEY (cpu_model_id) REFERENCES model (id);
ALTER TABLE machine_specs MODIFY (cpu_model_id CONSTRAINT machine_specs_cpu_model_id_nn NOT NULL);

DROP TABLE cpu;
DROP SEQUENCE cpu_id_seq;

CREATE INDEX machine_cpu_model_idx ON machine (cpu_model_id);
CREATE INDEX machine_specs_cpu_model_idx ON machine_specs (cpu_model_id);

QUIT;
