ALTER TABLE dynamic_stub ADD range_class VARCHAR(16);
UPDATE dynamic_stub SET range_class='vm' where range_class IS NULL;
ALTER TABLE dynamic_stub MODIFY (range_class CONSTRAINT "DYNAMIC_STUB_RANGE_CLASS_NN" NOT NULL);

QUIT;
