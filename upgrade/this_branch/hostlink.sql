CREATE TABLE hostlink (
        id INTEGER CONSTRAINT hostlink_id_nn NOT NULL, 
        target VARCHAR(255) CONSTRAINT hostlink_target_nn NOT NULL, 
        owner VARCHAR(32) CONSTRAINT hostlink_owner_nn NOT NULL, 
        CONSTRAINT hostlink_pk PRIMARY KEY (id), 
        CONSTRAINT hostlink_resource_fk FOREIGN KEY(id) REFERENCES "resource" (id) ON DELETE CASCADE
);

COMMIT;
