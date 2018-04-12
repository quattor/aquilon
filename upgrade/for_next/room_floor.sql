ALTER TABLE room ADD floor VARCHAR2(16);
UPDATE room SET floor='0';
ALTER TABLE room MODIFY (floor CONSTRAINT room_floor_nn NOT NULL);

QUIT;