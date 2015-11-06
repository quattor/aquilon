template personality/vulcan-10g-server-prod/config;

variable PERSONALITY = "vulcan-10g-server-prod";
include { "personality/config" };

# Hack to make the tests run
include { if_exists("features/vulcan/v1-10g-server-prod/config"); };
include { if_exists("features/version/vcenter/41/config"); };
include { if_exists("features/version/esx_host/41/config"); };
