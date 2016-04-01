from bauhaus.workflows.secondary import *
from bauhaus.workflows.tertiary  import *

_workflows = [
    # Secondary
    BasicMappingWorkflow,
    ChunkedMappingWorkflow,
    VariantCallingWorkflow,
    CoverageTitrationWorkflow,
    # Tertiary
    CoverageTitrationReportsWorkflow ]

availableWorkflows = \
    { wf.name() : wf
      for wf in _workflows }
