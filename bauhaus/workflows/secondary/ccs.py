__all__ = [ "BasicCCSWorkflow",
            "ChunkedCCSWorkflow",
            "CCSMappingWorkflow",
            "CCSMappingReportsWorkflow" ]

import os.path as op

from bauhaus.experiment import InputType, ConditionTable, ResequencingConditionTable
from bauhaus import Workflow
from .datasetOps import movieName

def genCCS(pflow, subreadSets):
    ccsRule = pflow.genRuleOnce(
        "ccs",
        "$gridSMP $ncpus ccs --numThreads=$ncpus $in $outBam && " +
        "dataset create $outBam $out")
    ccsSets = []
    for subreadSet in subreadSets:
        with pflow.context("movieName", movieName(subreadSet)):
            outBam = pflow.formatInContext("{condition}/ccs/{movieName}.ccs.bam")
            buildVariables = dict(outBam=outBam, ncpus=8)
            ccsSets.extend(pflow.genBuildStatement(
                ["{condition}/ccs/{movieName}.consensusreadset.xml"],
                "ccs",
                [subreadSet],
                buildVariables))
    return ccsSets


# -- CCS
class BasicCCSWorkflow(Workflow):
    """
    Basic CCS---not chunked, just dead simple.
    """
    @staticmethod
    def name():
        return "BasicCCS"

    @staticmethod
    def conditionTableType():
        return ConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                assert ct.inputType == InputType.SubreadSet # TODO: move to validation.
                outputDict[condition] = genCCS(pflow, ct.inputs(condition))
        return outputDict


class ChunkedCCSWorkflow(Workflow):
    """
    Chunked CCS---split up into multiple jobs
    """
    @staticmethod
    def name():
        return "ChunkedCCS"

    @staticmethod
    def conditionTableType():
        return ConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        return outputDict



# -- CCS mapping + reports
class CCSMappingWorkflow(Workflow):
    pass


# -- CCS mapping + reports
class CCSMappingReportsWorkflow(Workflow):
    pass
