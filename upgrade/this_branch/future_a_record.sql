
CREATE TABLE future_a_record (
        system_id INTEGER NOT NULL,
        CONSTRAINT future_a_record_pk PRIMARY KEY (system_id),
        CONSTRAINT future_a_record_system_fk FOREIGN KEY(system_id) REFERENCES system (id) ON DELETE CASCADE
);

commit;
