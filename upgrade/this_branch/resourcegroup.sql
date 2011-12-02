CREATE TABLE resourcegroup (
        id INTEGER CONSTRAINT resourcegroup_id_nn NOT NULL,
        CONSTRAINT resourcegroup_pk PRIMARY KEY (id),
        CONSTRAINT rg_resource_fk FOREIGN KEY(id) REFERENCES "resource" (id) ON DELETE CASCADE
);
COMMIT;

