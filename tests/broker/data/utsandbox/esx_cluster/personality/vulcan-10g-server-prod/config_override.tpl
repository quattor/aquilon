template personality/vulcan-10g-server-prod/config_override;

# Hack to make the tests run
include { if_exists("features/vulcan/v1-10g-server-prod/config"); };
include { if_exists("features/version/vcenter/50/config"); };
include { if_exists("features/version/esx_host/50/config"); };
