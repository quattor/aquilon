CREATE TABLE hostlink (
        id INTEGER CONSTRAINT hostlink_id_nn NOT NULL,
        target VARCHAR(255) CONSTRAINT hostlink_target_nn NOT NULL,
        owner_user VARCHAR(32) CONSTRAINT hostlink_owner_user_nn NOT NULL,
        owner_group VARCHAR(32),
        CONSTRAINT hostlink_pk PRIMARY KEY (id),
        CONSTRAINT hostlink_resource_fk FOREIGN KEY(id) REFERENCES "resource" (id) ON DELETE CASCADE
);

COMMIT;
