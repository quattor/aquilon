ALTER TABLE share ADD latency_threshold NUMBER(*,0);

UPDATE share SET latency_threshold = 20;
COMMIT;
QUIT;
