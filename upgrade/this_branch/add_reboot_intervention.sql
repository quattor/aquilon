CREATE TABLE reboot_intervention (
        id INTEGER CONSTRAINT reboot_intervention_id_nn NOT NULL,
        CONSTRAINT reboot_intervention_pk PRIMARY KEY (id),
        CONSTRAINT ri_resource_fk FOREIGN KEY(id) REFERENCES intervention (id) ON DELETE CASCADE
);

QUIT;

