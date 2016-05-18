__all__ = [ "BasicMappingWorkflow", "ChunkedMappingWorkflow"]

import os.path as op

from bauhaus import Workflow
from .datasetOps import *
from bauhaus.experiment import (InputType, ResequencingConditionTable)



# These will be run within a condition...

def genSubreads(pflow, remoteSubreadSets):
    """
    Copy subreads to the workflow dir, while fixing relative paths
    """
    copyRule = pflow.genRuleOnce(
        "copySubreadsDataset",
        "dataset create $in $out")
    for rss in remoteSubreadSets:
        localName = "{condition}/subreads/%s" % bn
        bn = op.basename(rss)
        subreadCopyStmt = pflow.genBuildStatement(
            ["{condition}/subreads/%s" % bn],
            "copyRule"
            [rss])

def genSubreadsFromH5(pflow, remoteBaxen):
    pass


# ----

class BasicSubreadsWorflow(Workflow)
    """
    Generate subreads datasets under a directory here.

    When the original input is BAM this is effectively just a copy
    (while fixing relative paths); when the original input is HDF5, we
    bax2bam it here.
    """
    @staticmethod
    def name():
        return "BasicSubreads"

    @staticmethod
    def conditionTableType():
        return conditionTableType

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                if ct.inputType == InputType.SubreadSet:
                    remoteSubreadSets = ct.inputs(condition)
                elif ct.inputType == InputType.HDF5Subreads:
                    # bax2bam it

                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict
