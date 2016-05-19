from bauhaus.workflows.secondary import *
from bauhaus.workflows.tertiary  import *

_workflows = [ eval(wfName)
               for wfName in dir()
               if wfName.endswith("Workflow") ]

availableWorkflows = \
    { wf.name() : wf
      for wf in _workflows }
