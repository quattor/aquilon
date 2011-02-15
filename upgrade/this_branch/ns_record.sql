CREATE TABLE ns_record (
    a_record_id INTEGER CONSTRAINT "NS_RECORD_A_RECORD_ID_NN" NOT NULL ENABLE,
    dns_domain_id INTEGER CONSTRAINT "NS_RECORD_DNS_DOMAIN_ID_NN" NOT NULL ENABLE,
    creation_date DATE CONSTRAINT "NS_RECORD_CR_DATE_NN" NOT NULL ENABLE,
    comments VARCHAR2(255 CHAR),
    CONSTRAINT ns_record_pk PRIMARY KEY (a_record_id, dns_domain_id),
    CONSTRAINT ns_record_a_record_fk FOREIGN KEY(a_record_id) REFERENCES future_a_record (system_id),
    CONSTRAINT ns_record_domain_fk FOREIGN KEY(dns_domain_id) REFERENCES dns_domain (id)
);

commit;
