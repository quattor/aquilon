CREATE TABLE location_link (
        child_id INTEGER NOT NULL,
        parent_id INTEGER NOT NULL,
        distance INTEGER NOT NULL,
        CONSTRAINT "LOCATION_LINK_PK" PRIMARY KEY (child_id, parent_id),
        CONSTRAINT "LINK_CHILD_LOCATION_FK" FOREIGN KEY(child_id) REFERENCES location (id) ON DELETE CASCADE,
        CONSTRAINT "LINK_PARENT_LOCATION_FK" FOREIGN KEY(parent_id) REFERENCES location (id) ON DELETE CASCADE
);
