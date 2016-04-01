from bauhaus.workflows.secondary import *

availableWorkflows = \
    { "BasicMapping"             : genMappingWorkflow,
      "ChunkedMapping"           : genChunkedMappingWorkflow,
      "VariantCalling"           : genVariantCallingWorkflow,
      "CoverageTitration"        : genCoverageTitrationWorkflow,
      "CoverageTitrationReports" : genCoverageTitrationReportsWorkflow }
