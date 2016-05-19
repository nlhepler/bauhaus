__all__ = [ "BasicSubreadsWorkflow" ]

import os.path as op

from bauhaus import Workflow
from .datasetOps import *
from bauhaus.experiment import (InputType, ConditionTable)

# These will be run within a condition...

def genSubreads(pflow, remoteSubreadSets):
    """
    Copy subreads to the workflow dir, while fixing relative paths
    """
    copyRule = pflow.genRuleOnce(
        "copySubreadsDataset",
        "dataset create $out $in")
    localSubreadSets = []
    for rss in remoteSubreadSets:
        bn = op.basename(rss)
        localName = "{condition}/subreads/%s" % bn
        subreadCopyStmt = pflow.genBuildStatement(
            ["{condition}/subreads/%s" % bn],
            "copySubreadsDataset",
            [rss])
        localSubreadSets.extend(subreadCopyStmt.outputs)
    return localSubreadSets

# ----

class BasicSubreadsWorkflow(Workflow):
    """
    Generate subreads datasets under a directory within the worfkflow,
    fixing relative paths
    """
    @staticmethod
    def name():
        return "BasicSubreads"

    @staticmethod
    def conditionTableType():
        return ConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                if ct.inputType == InputType.SubreadSet:
                    remoteSubreadSets = ct.inputs(condition)
                    localSubreadSets = genSubreads(pflow, remoteSubreadSets)
                    outputDict[condition] = localSubreadSets
                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict
