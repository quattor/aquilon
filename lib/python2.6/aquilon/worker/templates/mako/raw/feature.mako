<%
from aquilon.aqdb.model import HardwareFeature, InterfaceFeature
from aquilon.worker.templates.panutils import pan
%>
% if record.feature.comments:
# ${record.feature.comments}
% endif
% if isinstance(record.feature, HardwareFeature):
include {
	if ((value("/hardware/manufacturer") == "${record.model.vendor}") &&
            (value("/hardware/template_name") == "${record.model.name}")){
		return("${record.feature.cfg_path}")
	} else{ return(undef); };
};
"/metadata/features"={
	if ((value("/hardware/manufacturer") == "${record.model.vendor}") &&
            (value("/hardware/template_name") == "${record.model.name}")){
		append("${record.feature.cfg_path}/config");
	} else { SELF; };
};
% endif
% if isinstance(record.feature, InterfaceFeature):
variable CURRENT_INTERFACE = "${record.interface_name}";
% endif
% if not isinstance(record.feature, HardwareFeature):
include { "${record.feature.cfg_path}/config" };
"/metadata/features" = append("${record.feature.cfg_path}/config");
% endif
