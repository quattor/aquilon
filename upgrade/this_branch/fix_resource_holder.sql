ALTER TABLE "resource" MODIFY (holder_id INTEGER CONSTRAINT resource_holder_id_nn NOT NULL);

QUIT;
