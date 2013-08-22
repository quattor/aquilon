UPDATE host_grn_map SET TARGET = 'invited' where TARGET = 'hlmplus';
UPDATE personality_grn_map set TARGET = 'invited' where TARGET = 'hlmplus';

COMMIT;
QUIT;

