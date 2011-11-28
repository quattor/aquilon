CREATE TABLE resourcegroup (
        id INTEGER NOT NULL,
        CONSTRAINT resourcegroup_pk PRIMARY KEY (id),
        CONSTRAINT fs_resource_fk FOREIGN KEY(id) REFERENCES resource (id) ON DELETE CASCADE
)
COMMIT;