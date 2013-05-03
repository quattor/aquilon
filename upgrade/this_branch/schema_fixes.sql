ALTER TABLE "resource" RENAME CONSTRAINT resource_holder_id_nn TO "resource_HOLDER_ID_NN";
ALTER TABLE "share" RENAME CONSTRAINT "share_PK" TO share_pk;
ALTER TABLE "share" RENAME CONSTRAINT "share_RESOURCE_FK" TO share_resource_fk;
ALTER INDEX "share_PK" RENAME TO share_pk;
