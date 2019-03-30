ALTER TABLE hostlink MODIFY(target NULL);

CREATE TABLE hostlink_parent_map (
        resource_id INTEGER NOT NULL,
        parent VARCHAR2(32 CHAR) NOT NULL,
        CONSTRAINT hostlink_parent_map_pk PRIMARY KEY (resource_id, parent),
        CONSTRAINT hl_prnt_map_resource_fk FOREIGN KEY(resource_id) REFERENCES "resource" (id) ON DELETE CASCADE
);
