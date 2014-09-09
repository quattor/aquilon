UPDATE vlan_info SET port_group = 'transit-v717', vlan_type = 'transit' WHERE vlan_id = 717;
UPDATE vlan_info SET port_group = 'transit-v718', vlan_type = 'transit' WHERE vlan_id = 718;
UPDATE port_group SET usage = 'transit' WHERE usage = 'vcs';
UPDATE interface SET port_group_name = 'transit-v717' WHERE port_group_name = 'vcs-v717';
UPDATE interface SET port_group_name = 'transit-v718' WHERE port_group_name = 'vcs-v718';

COMMIT;

QUIT;
