/* create tables */
CREATE TABLE param_def_holder (
        id INTEGER NOT NULL,
        type VARCHAR(64) NOT NULL,
        creation_date DATE NOT NULL,
        archetype_id INTEGER,
        feature_id INTEGER,
        CONSTRAINT param_def_holder_pk PRIMARY KEY (id),
        CONSTRAINT param_def_holder_archetype_fk FOREIGN KEY(archetype_id) REFERENCES archetype (id) ON DELETE CASCADE,
        CONSTRAINT param_def_holder_feature_fk FOREIGN KEY(feature_id) REFERENCES feature (id) ON DELETE CASCADE
);
CREATE TABLE param_definition (
        id INTEGER NOT NULL,
        path VARCHAR(255) NOT NULL,
        template VARCHAR(32),
        required INTEGER NOT NULL,
        value_type VARCHAR(16) NOT NULL,
        "default" CLOB,
        description VARCHAR(255),
        holder_id INTEGER,
        creation_date DATE NOT NULL,
        CONSTRAINT param_definition_pk PRIMARY KEY (id),
        CONSTRAINT param_definition_paramdef_ck CHECK (required IN (0, 1)),
        CONSTRAINT param_definition_holder_fk FOREIGN KEY(holder_id) REFERENCES param_def_holder (id) ON DELETE CASCADE
);
CREATE TABLE param_holder (
        id INTEGER NOT NULL,
        creation_date DATE NOT NULL,
        holder_type VARCHAR(64) NOT NULL,
        personality_id INTEGER,
        featurelink_id INTEGER,
        CONSTRAINT param_holder_pk PRIMARY KEY (id),
        CONSTRAINT param_holder_persona_fk FOREIGN KEY(personality_id) REFERENCES personality (id) ON DELETE CASCADE,
        CONSTRAINT param_holder_featurelink_fk FOREIGN KEY(featurelink_id) REFERENCES feature_link (id) ON DELETE CASCADE
);
CREATE TABLE parameter (
        id INTEGER NOT NULL,
        value CLOB,
        creation_date DATE NOT NULL,
        comments VARCHAR(255),
        holder_id INTEGER,
        CONSTRAINT parameter_pk PRIMARY KEY (id),
        CONSTRAINT parameter_paramholder_fk FOREIGN KEY(holder_id) REFERENCES param_holder (id) ON DELETE CASCADE
);

CREATE SEQUENCE PARAMETER_SEQ;
CREATE SEQUENCE PARAM_DEFINITION_SEQ;
CREATE SEQUENCE PARAM_DEF_HOLDER_SEQ;
CREATE SEQUENCE PARAM_HOLDER_SEQ;

COMMIT;
QUIT;
