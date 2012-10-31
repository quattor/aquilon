template archetype/final;

include "components/spma/functions";

"/software/components/resolver/search" = {
	if (exists("/hardware/sysloc/dns_search_domains")) {
		domains = value("/hardware/sysloc/dns_search_domains");
	} else {
		domains = list();
	};
	domains[length(domains)] = "ms.com";
	return(domains);
};
