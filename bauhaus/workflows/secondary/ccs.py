__all__ = [ "BasicCCSWorkflow",
            "ChunkedCCSWorkflow",
            "CCSMappingWorkflow",
            "CCSMappingReportsWorkflow" ]

import os.path as op

from bauhaus.experiment import InputType, ConditionTable, ResequencingConditionTable
from bauhaus import Workflow
from bauhaus.utils import listConcat

from .datasetOps import *
from .mapping import genMappingCCS

def genCCS(pflow, subreadSets):
    ccsRule = pflow.genRuleOnce(
        "ccs",
        "$gridSMP $ncpus ccs --pbi --force --numThreads=$ncpus $in $outBam && " +
        "dataset create --type ConsensusReadSet $out $outBam")
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

def genChunkedCCS(pflow, subreadSets, splitFactor=8, doMerge=True):
    ccsRule = pflow.genRuleOnce(
        "ccs",
        "$gridSMP $ncpus ccs --pbi --force --numThreads=$ncpus $in $outBam && " +
        "dataset create --type ConsensusReadSet $out $outBam")
    ccsSets = []
    for subreadSet in subreadSets:
        with pflow.context("movieName", movieName(subreadSet)):
            ccsSetChunks = []
            subreadSetChunks = genSubreadSetSplit(pflow, subreadSet, splitFactor)
            for (i, subreadSetChunk) in enumerate(subreadSetChunks):
                with pflow.context("chunkNum", i):
                    outBam = pflow.formatInContext("{condition}/ccs_chunks/{movieName}.chunk{chunkNum}.ccs.bam")
                    buildVariables = dict(outBam=outBam, ncpus=8)
                    buildStmt = pflow.genBuildStatement(
                        ["{condition}/ccs_chunks/{movieName}.chunk{chunkNum}.consensusreadset.xml"],
                        "ccs",
                        [subreadSetChunk],
                        buildVariables)
                    ccsSetChunks.extend(buildStmt.outputs)
            # Consolidate or merge the CCS chunks from this movie
            if doMerge:
                ccsSets.extend(
                    genDatasetConsolidateForMovie(pflow, ccsSetChunks, "ccs", "consensusreadset"))
            else:
                ccsSets.extend(ccsSetChunks)
    # Merge for the condition
    if doMerge:
        return genDatasetMergeForCondition(pflow, ccsSets, "ccs", "consensusreadset")
    else:
        return ccsSets


def genCCSAndMapping(pflow, subreadSets, reference):
    ccsSets = genChunkedCCS(pflow, subreadSets, doMerge=False)
    alignmentSets = genMappingCCS(pflow, ccsSets, reference)
    return alignmentSets


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
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                assert ct.inputType == InputType.SubreadSet # TODO: move to validation.
                outputDict[condition] = genChunkedCCS(pflow, ct.inputs(condition))
        return outputDict


# -- CCS mapping
class CCSMappingWorkflow(Workflow):
    """
    CCS + mapping
    """
    @staticmethod
    def name():
        return "CCSMapping"

    @staticmethod
    def conditionTableType():
        return ResequencingConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                assert ct.inputType == InputType.SubreadSet # TODO: move to validation.
                outputDict[condition] = genCCSAndMapping(pflow, ct.inputs(condition), ct.reference(condition))
        return outputDict



# -- CCS mapping + reports
class CCSMappingReportsWorkflow(Workflow):

    @staticmethod
    def name():
        return "CCSMappingReports"

    @staticmethod
    def conditionTableType():
        return ResequencingConditionTable

    def generate(self, pflow, ct):
        pflow.bundleScript("R/ccsMappingPlots.R")
        ccsMappingOutputs = CCSMappingWorkflow().generate(pflow, ct)
        flatOutputs = listConcat(ccsMappingOutputs.values())

        ccsSummaryRule = pflow.genRuleOnce(
            "ccsMappingSummaryAnalysis",
            "Rscript --vanilla R/ccsMappingPlots.R .")
        bs = pflow.genBuildStatement(
            [ "ccs-mapping.pdf"],
            "ccsMappingSummaryAnalysis",
            flatOutputs)
