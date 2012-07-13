-- Add new node_index column to the host_cluster_member table

ALTER TABLE host_cluster_member ADD node_index INTEGER;

-- Now backfill values for all existing clusters
DECLARE
 CURSOR hcm_curs IS SELECT * FROM host_cluster_member 
   WHERE node_index IS NULL FOR UPDATE;
 BEGIN
 FOR hcm IN hcm_curs LOOP
    UPDATE host_cluster_member set node_index=1+(
           select nvl(max(node_index),0) from host_cluster_member
           where cluster_id=hcm.cluster_id)
    WHERE CURRENT OF hcm_curs;
 END LOOP;
END;
/
COMMIT;

-- Finally add the constraint to prevent it being null
ALTER TABLE host_cluster_member MODIFY (node_index INTEGER CONSTRAINT host_clstr_mmbr_node_index_nn NOT NULL);

ALTER TABLE host_cluster_member ADD CONSTRAINT host_cluster_member_node_uk UNIQUE (cluster_id, node_index);

QUIT;