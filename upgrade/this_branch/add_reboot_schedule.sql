CREATE TABLE reboot_schedule (
        id INTEGER CONSTRAINT reboot_schedule_id_nn  NOT NULL,
        time VARCHAR(5 CHAR),
        week VARCHAR(16 CHAR) CONSTRAINT reboot_schedule_week_nn NOT NULL,
        day VARCHAR(32 CHAR) CONSTRAINT reboot_schedule_day_nn NOT NULL,
        CONSTRAINT reboot_schedule_pk PRIMARY KEY (id),
        CONSTRAINT rs_resource_fk FOREIGN KEY(id) REFERENCES "resource" (id) ON DELETE CASCADE
);

QUIT;

