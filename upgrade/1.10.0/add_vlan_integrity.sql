ALTER TABLE observed_vlan ADD CONSTRAINT obs_vlan_vlan_fk FOREIGN KEY(vlan_id) REFERENCES vlan_info (vlan_id);
