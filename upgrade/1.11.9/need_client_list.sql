ALTER TABLE service ADD need_client_list INTEGER;
ALTER TABLE service ADD CONSTRAINT service_need_client_list_ck CHECK (need_client_list IN (0, 1));
UPDATE service SET need_client_list = 1;
ALTER TABLE service MODIFY (need_client_list INTEGER CONSTRAINT service_need_client_list_nn NOT NULL);

QUIT;
