CREATE SEQUENCE fqdn_id_seq;
CREATE TABLE fqdn (
	id INTEGER CONSTRAINT "FQDN_ID_NN" NOT NULL,
	name VARCHAR2(63 CHAR) CONSTRAINT "FQDN_NAME_NN" NOT NULL,
	dns_domain_id INTEGER CONSTRAINT "FQDN_DNS_DOMAIN_ID_NN" NOT NULL,
	dns_environment_id INTEGER CONSTRAINT "FQDN_DNS_ENV_ID_NN" NOT NULL,
	creation_date DATE CONSTRAINT "FQDN_CR_DATE_NN" NOT NULL,
	CONSTRAINT "FQDN_PK" PRIMARY KEY (id),
	CONSTRAINT "FQDN_NAME_DOMAIN_ENV_UK" UNIQUE (name, dns_domain_id, dns_environment_id),
	CONSTRAINT "FQDN_DNS_DOMAIN_FK" FOREIGN KEY (dns_domain_id) REFERENCES dns_domain (id),
	CONSTRAINT "FQDN_DNS_ENV_FK" FOREIGN KEY (dns_environment_id) REFERENCES dns_environment (id)
);

ALTER TABLE dns_record ADD fqdn_id INTEGER;

VARIABLE fqdn_id_var NUMBER;
DECLARE
	dns_rec dns_record%ROWTYPE;
	CURSOR dns_curs IS SELECT * FROM dns_record FOR UPDATE;
BEGIN
	OPEN dns_curs;
	LOOP
		FETCH dns_curs INTO dns_rec;
		EXIT WHEN dns_curs%NOTFOUND;
		SELECT fqdn_id_seq.NEXTVAL INTO :fqdn_id_var FROM DUAL;
		INSERT INTO fqdn (id, name, dns_domain_id, dns_environment_id, creation_date)
			VALUES (:fqdn_id_var, dns_rec.name, dns_rec.dns_domain_id,
				dns_rec.dns_environment_id, dns_rec.creation_date);
		UPDATE dns_record SET fqdn_id = :fqdn_id_var WHERE CURRENT OF dns_curs;
	END LOOP;
	CLOSE dns_curs;
END;

/

ALTER TABLE dns_record
	MODIFY (fqdn_id CONSTRAINT "DNS_RECORD_FQDN_ID_NN" NOT NULL);
ALTER TABLE dns_record
	ADD CONSTRAINT "DNS_RECORD_FQDN_FK" FOREIGN KEY (fqdn_id) REFERENCES fqdn (id);

ALTER TABLE dns_record DROP CONSTRAINT "DNS_RECORD_NAME_DOMAIN_ENV_UK";
ALTER TABLE dns_record DROP CONSTRAINT "DNS_RECORD_DNS_DOMAIN_FK";
ALTER TABLE dns_record DROP CONSTRAINT "DNS_RECORD_DNS_ENV_FK";
ALTER TABLE dns_record DROP COLUMN name;
ALTER TABLE dns_record DROP COLUMN dns_domain_id;
ALTER TABLE dns_record DROP COLUMN dns_environment_id;

COMMIT;
QUIT;
