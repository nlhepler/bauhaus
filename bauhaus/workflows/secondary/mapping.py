__all__ = [ "BasicMappingWorkflow", "ChunkedMappingWorkflow" ]

import os.path as op

from bauhaus import Workflow
from .datasetOps import *
from bauhaus.experiment import (InputType, ResequencingConditionTable)

# Conventions (in the absence of types!):
#
#   - Every generator should returns the list of context-resolved
#     outputs from its final build statement
#


# ----------- Mapping --------------------


# Assumption that should be asserted: each input subreads set comes from a separate movie.

def genMapping(pflow, subreadsSets, reference):
    """
    Map the subreads set, without chunking.  This is painfully slow on
    Sequel-scale data.
    """
    mapRule = pflow.genRuleOnce(
        "map",
        "$gridSMP $ncpus pbalign --nproc $ncpus $in $reference $out")
    alignmentSets = []
    for subreadsSet in subreadsSets:
        with pflow.context("movieName", movieName(subreadsSet)):
            buildVariables = dict(reference=reference, ncpus=8)
            alignmentSets.extend(pflow.genBuildStatement(
                ["{condition}/mapping/{movieName}.alignmentset.xml"],
                "map",
                [subreadsSet],
                buildVariables).outputs)
    return genAlignmentSetMergeForCondition(pflow, alignmentSets)


def genChunkedMapping(pflow, subreadsSets, reference, splitFactor=8):
    """
    Break the subreads set into chunks, map the chunks, then
    consolidate the mapped chunks
    """
    mapRule = pflow.genRuleOnce(
        "map",
        "$gridSMP $ncpus pbalign --nproc $ncpus $in $reference $out")
    alignmentSets = []
    for subreadsSet in subreadsSets:
        with pflow.context("movieName", movieName(subreadsSet)):
            alignmentSetChunks = []
            subreadsSetChunks = genSubreadsSetSplit(pflow, subreadsSet, splitFactor)
            for (i, subreadsSetChunk) in enumerate(subreadsSetChunks):
                with pflow.context("chunkNum", i):
                    buildVariables = dict(reference=reference, ncpus=8)
                    buildStmt = pflow.genBuildStatement(
                        ["{condition}/mapping_chunks/{movieName}.chunk{chunkNum}.alignmentset.xml"],
                        "map",
                        [subreadsSetChunk],
                        buildVariables)
                    alignmentSetChunks.extend(buildStmt.outputs)
            alignmentSets.extend(genAlignmentSetConsolidateForMovie(pflow, alignmentSetChunks))
    return genAlignmentSetMergeForCondition(pflow, alignmentSets)


# ---------- Workflows -------------
# Unlike the generators above, these guys return a dict of Condition -> resolved outputs
# These really ought to be codified using types.  Damn you Python.
# TODO: do we consider these "tertiary"?

class BasicMappingWorkflow(Workflow):
    """
    Basic mapping---not chunked, just dead simple.
    """
    @staticmethod
    def name():
        return "BasicMapping"

    @staticmethod
    def conditionTableType():
        return ResequencingConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                reference = ct.reference(condition)
                if ct.inputType == InputType.SubreadSet:
                    subreadsSets = ct.inputs(condition)
                    outputDict[condition] = genMapping(pflow, subreadsSets, reference)
                elif ct.inputType == InputType.AlignmentSet:
                    outputDict[condition] = genAlignmentSetMergeForCondition(pflow, ct.inputs(condition))
                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict



class ChunkedMappingWorkflow(Workflow):
    """
    Chunked mapping
    """
    @staticmethod
    def name():
        return "ChunkedMapping"

    @staticmethod
    def conditionTableType():
        return ResequencingConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                reference = ct.reference(condition)
                if ct.inputType == InputType.SubreadSet:
                    subreadsSets = ct.inputs(condition)
                    outputDict[condition] = genChunkedMapping(pflow, subreadsSets, reference, splitFactor=8)
                elif ct.inputType == InputType.AlignmentSet:
                    outputDict[condition] = genAlignmentSetMergeForCondition(pflow, ct.inputs(condition))
                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict



# -------------------- Demo -------------------

# lambda short insert ecoli runs intended for CCS analysis
if __name__ == '__main__':
    from bauhaus.pflow import PFlow
    inputDataByCondition = { "Replicate1" : ["/pbi/collections/315/3150128/r54008_20160308_001811/1_A01/m54008_160308_002050.subreadset.xml"],
                             "Replicate2" : ["/pbi/collections/315/3150128/r54008_20160308_001811/2_B01/m54008_160308_053311.subreadset.xml"] }

    reference = "/mnt/secondary/iSmrtanalysis/current/common/references/lambdaNEB/sequence/lambdaNEB.fasta"

    pflow = PFlow()
    for (condition, inputSubreadSets) in inputDataByCondition.iteritems():
        with pflow.context("condition", condition):
            #genMapping(pflow, inputSubreadSets, reference)
            genChunkedMapping(pflow, inputSubreadSets, reference, 8)
    pflow.write("build.ninja")
