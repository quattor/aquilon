
CREATE TABLE observed_vlan (
    switch_id INTEGER NOT NULL, 
    network_id INTEGER NOT NULL, 
    vlan_id INTEGER NOT NULL, 
    creation_date DATE NOT NULL, 
    CONSTRAINT observed_vlan_pk PRIMARY KEY (switch_id, network_id, vlan_id), 
    CONSTRAINT obs_vlan_hw_fk FOREIGN KEY(switch_id) REFERENCES tor_switch (id) ON DELETE CASCADE, 
    CONSTRAINT "OBSERVED_VLAN_MAX_VLAN_ID"  CHECK ("VLAN_ID" < 4096), 
    CONSTRAINT obs_vlan_net_fk FOREIGN KEY(network_id) REFERENCES network (id) ON DELETE CASCADE
);

commit;


CREATE TABLE vlan_info (
    vlan_id INTEGER NOT NULL, 
    port_group VARCHAR(32) NOT NULL, 
    vlan_type VARCHAR(32) NOT NULL, 
    CONSTRAINT vlan_info_pk PRIMARY KEY (vlan_id), 
    CONSTRAINT vlan_info_port_group_uk  UNIQUE (port_group), 
    CONSTRAINT "VLAN_INFO_MAX_VLAN_ID"  CHECK ("VLAN_ID" < 4096)
);

commit;

INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (701, 'storage-v701', 'storage');
INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (702, 'vmotion-v702', 'vmotion');
INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (710, 'user-v710', 'user');
INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (711, 'user-v711', 'user');
INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (712, 'user-v712', 'user');
INSERT INTO VLAN_INFO (VLAN_ID, PORT_GROUP, VLAN_TYPE) VALUES (713, 'user-v713', 'user');

commit;

