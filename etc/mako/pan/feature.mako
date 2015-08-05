<%
from aquilon.aqdb.model import HardwareFeature, InterfaceFeature
%>
% if record.feature.comments:
# ${record.feature.comments}
% endif
% if isinstance(record.feature, InterfaceFeature):
variable CURRENT_INTERFACE = "${record.interface_name}";
% endif
% if isinstance(record.feature, HardwareFeature):
include {
    if ((value("/hardware/manufacturer") == "${record.model.vendor}") &&
	(value("/hardware/template_name") == "${record.model.name}")) {
	if (exists("${record.feature.cfg_path}/config")) {
	    "${record.feature.cfg_path}/config";
	} else {
	    "${record.feature.cfg_path}";
	};
    } else {
	undef;
    };
};
"/metadata/features" = {
    if ((value("/hardware/manufacturer") == "${record.model.vendor}") &&
	(value("/hardware/template_name") == "${record.model.name}")) {
	append("${record.feature.cfg_path}/config");
    } else {
	SELF;
    };
};
% else:
include { "${record.feature.cfg_path}/config" };
"/metadata/features" = append("${record.feature.cfg_path}/config");
% endif
