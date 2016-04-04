from bauhaus.workflows.secondary import *
from bauhaus.workflows.tertiary  import *

_workflows = [
    # Secondary
    BasicMappingWorkflow,
    ChunkedMappingWorkflow,
    VariantCallingWorkflow,
    CoverageTitrationWorkflow,
    BasicCCSWorkflow,
    ChunkedCCSWorkflow,
    CCSMappingWorkflow,
    # Tertiary
    CoverageTitrationReportsWorkflow ]

availableWorkflows = \
    { wf.name() : wf
      for wf in _workflows }
