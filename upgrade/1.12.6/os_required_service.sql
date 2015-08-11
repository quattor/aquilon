CREATE TABLE os_service_list_item (
	service_id INTEGER CONSTRAINT os_service_list_item_svc_id_nn NOT NULL,
	operating_system_id INTEGER CONSTRAINT os_service_list_item_os_id_nn NOT NULL,
	CONSTRAINT os_service_list_item_pk PRIMARY KEY (service_id, operating_system_id),
	CONSTRAINT os_service_list_item_svc_fk FOREIGN KEY(service_id) REFERENCES service (id),
	CONSTRAINT os_service_list_item_os_fk FOREIGN KEY(operating_system_id) REFERENCES operating_system (id) ON DELETE CASCADE
);

CREATE INDEX os_service_list_item_os_idx ON os_service_list_item (operating_system_id);

QUIT;
