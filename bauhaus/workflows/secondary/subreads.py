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
        "dataset create $in $out")
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

def genSubreadsFromH5(pflow, remoteBaxen):
    raise NotImplementedError


# ----

class BasicSubreadsWorkflow(Workflow):
    """
    Generate subreads datasets under a directory within the worfkflow.

    When the original input is BAM this is effectively just a copy
    (while fixing relative paths); when the original input is HDF5, we
    bax2bam it here.
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
                elif ct.inputType == InputType.HDF5Subreads:
                    # bax2bam it
                    raise NotImplementedError
                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict
