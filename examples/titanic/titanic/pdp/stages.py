import typing as tp
import inspect

import colt
import pandas as pd
import pdpipe as pdp

from titanic.utils.camsnake import camel_to_snake


class PdpStage(pdp.PdPipelineStage, colt.Registrable):
    # pylint: disable=abstract-method
    pass


# register PdPipeStages in pdpipe
for pdpname, pdpcls in inspect.getmembers(pdp):
    if isinstance(pdpcls, type) and issubclass(pdpcls, pdp.PdPipelineStage):
        name = f"{camel_to_snake(pdpname)}"
        PdpStage.register(name)(pdpcls)


@PdpStage.register("pd_pipeline", exist_ok=True)
class PdPipelineWrapper(pdp.PdPipeline):
    def __init__(self, stages: tp.List[PdpStage], **kwargs) -> None:
        super().__init__(stages, **kwargs)
