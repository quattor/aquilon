CREATE TABLE address_alias (
        dns_record_id INTEGER CONSTRAINT "ADDRESS_ALIAS_DNS_RECORD_ID_NN" NOT NULL,
        target_id INTEGER CONSTRAINT "ADDRESS_ALIAS_TARGET_ID_NN" NOT NULL,
        CONSTRAINT address_alias_pk PRIMARY KEY (dns_record_id),
        CONSTRAINT address_alias_dns_record_fk FOREIGN KEY(dns_record_id) REFERENCES dns_record (id) ON DELETE CASCADE,
        CONSTRAINT address_alias_target_fk FOREIGN KEY(target_id) REFERENCES fqdn (id)
);

CREATE INDEX address_alias_target_idx ON address_alias (target_id);

QUIT;
