#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "..", "lib", "python2.6"))

# avoid the warning on deprecated md5 module. will remove when
# a later version of twisted handles this
import warnings
warnings.simplefilter("ignore", DeprecationWarning)


import aquilon.worker.depends
import aquilon.aqdb.depends

from twisted.scripts import twistd

from aquilon.twisted_patches import updated_application_run


twistd._SomeApplicationRunner.run = updated_application_run
twistd.run()
