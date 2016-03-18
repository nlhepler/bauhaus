from bauhaus.workflows.secondary import *

availableWorkflows = \
    { "Mapping"           : genMappingWorkflow,
      "ChunkedMapping"    : genChunkedMappingWorkflow,
      "VariantCalling"    : genVariantCallingWorkflow,
      "CoverageTitration" : genCoverageTitrationWorkflow }
