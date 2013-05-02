ALTER TABLE interface DROP CONSTRAINT iface_vlan_ck;
ALTER TABLE interface ADD CONSTRAINT iface_vlan_ck CHECK (parent_id IS NOT NULL AND vlan_id > 0 AND vlan_id < 4096 OR interface_type != 'vlan');
ALTER TABLE observed_vlan DROP CONSTRAINT observed_vlan_max_vlan_id_ck;
ALTER TABLE observed_vlan DROP CONSTRAINT observed_vlan_min_vlan_id_ck;
ALTER TABLE observed_vlan ADD CONSTRAINT observed_vlan_vlan_id_ck CHECK (vlan_id >= 0 AND vlan_id < 4096);
ALTER TABLE "resource" RENAME CONSTRAINT resource_holder_id_nn TO "resource_HOLDER_ID_NN";
ALTER TABLE "share" RENAME CONSTRAINT "share_PK" TO share_pk;
ALTER TABLE "share" RENAME CONSTRAINT "share_RESOURCE_FK" TO share_resource_fk;
ALTER INDEX "share_PK" RENAME TO share_pk;
ALTER TABLE vlan_info DROP CONSTRAINT vlan_info_max_vlan_id_ck;
ALTER TABLE vlan_info DROP CONSTRAINT vlan_info_min_vlan_id_ck;
ALTER TABLE vlan_info ADD CONSTRAINT vlan_info_vlan_id_ck CHECK (vlan_id >= 0 AND vlan_id < 4096);

QUIT;
