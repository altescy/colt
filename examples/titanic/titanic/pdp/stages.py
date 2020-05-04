import inspect

import colt
import pandas as pd
import pdpipe as pdp

from titanic.utils.camsnake import camel_to_snake

# register PdPipeStages in pdpipe
for pdpname, pdpcls in inspect.getmembers(pdp):
    if isinstance(pdpcls, type) and issubclass(pdpcls, pdp.PdPipelineStage):
        name = f"pdp:{camel_to_snake(pdpname)}"
        colt.register(name)(pdpcls)
