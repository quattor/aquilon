ALTER TABLE machine ADD uuid RAW(16);
ALTER TABLE machine ADD CONSTRAINT machine_uuid_uk UNIQUE (uuid);

QUIT;
