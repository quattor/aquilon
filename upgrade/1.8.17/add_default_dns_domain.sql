ALTER TABLE location ADD default_dns_domain_id INTEGER;
ALTER TABLE location ADD CONSTRAINT location_dns_domain_fk FOREIGN KEY (default_dns_domain_id) REFERENCES dns_domain (id) ON DELETE SET NULL;

QUIT;
