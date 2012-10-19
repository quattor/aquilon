drop table CLUSTER_ALIGNED_SERVICE;

QUIT;

-- after that the following has to be issued as part of the TCM

-- aq add_required_service --service esx_management_server --archetype metacluster --justification tcm=TTTTTTTTTT
-- aq add_required_service --service esx_management_server --archetype esx_cluster --justification tcm=TTTTTTTTTT
-- aq add_required_service --service vmconsole --archetype metacluster --justification tcm=TTTTTTTTTT
