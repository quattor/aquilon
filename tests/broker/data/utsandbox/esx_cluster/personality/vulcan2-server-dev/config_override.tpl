template personality/vulcan2-server-dev/config_override;

# Hack to make the tests run
include if_exists("features/vulcan/v2-prod-server/config");
include if_exists("features/version/vcenter/50/config");
include if_exists("features/version/esx_host/50/config");
