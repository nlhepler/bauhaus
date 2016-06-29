from bauhaus import Workflow
from bauhaus.experiment import (InputType, UnrolledMappingConditionTable)

from .datasetOps import *

__all__ = ["UnrolledMappingWorkflow", "UnrolledNoHQMappingWorkfow"]

# --

# TODO: need unrolled references for asym and sym adapter types... sigh

def genUnrolledReads(pflow, subreadSets):
    # While these are not really "subreads", we create a subreadset
    # for them.  There is no model in our official ontology for
    # "unrolled reads" datasets.
    #
    # TODO: We could/should move away from this and use the BLASR
    #       direct unrolling support
    #
    # TODO: This does not work on chunked subreadSets!  the ppa tools
    #       in general don't respect datasets, they just operate on BAM
    #
    bam2bamUnrollRule = pflow.genRuleOnce(
        "unrollReads",
        "$gridSMP $ncpus bam2bam -j $ncpus --hqregion $subreadsIn $scrapsIn -o $outPrefix &&" +
        "dataset create --type SubreadSet $out $outBam")

    unrolledReadSets = []
    for subreadSet in subreadSets:
        with pflow.context("movieName", movieName(subreadSet)):
            unrolledReadSets.extend(pflow.genBuildStatement(
                ["{condition}/unrolled_reads/{movieName}.unrolledreadset.xml"],
                "unrollReads",
                [subreadSet],
                dict(outBam="{condition}/unrolled_reads/{movieName}.hqregions.bam",
                     outPrefix="{condition}/unrolled_reads/{movieName}",
                     subreadsIn=subreadsBam(subreadSet),
                     scrapsIn=scrapsBam(subreadSet))).outputs)
    return unrolledReadSets

def genUnrolledNoHQReads(pflow, subreadSets):
    pass


# TODO: There is a lot of duplication of code here with the mapping
# and splitting.  This is really not great; we need a better process.

def genUnrolledReadSetSplit(pflow, unrolledReadSet, splitFactor):
    # Split by ZMWs.  Returns: [dset]
    assert splitFactor >= 1
    pflow.genRuleOnce(
            "splitByZmw",
            "$grid dataset split --zmws --targetSize 1 --chunks %d --outdir $outdir $in" % (splitFactor,))
    movie = movieName(unrolledReadSet)
    splitOutputs =  [ "{condition}/unrolled_reads_chunks/%s.chunk%d.unrolledreadset.xml" % (movie, i)
                      for i in xrange(splitFactor) ]
    buildStmt = pflow.genBuildStatement(splitOutputs,
                                        "splitByZmw",
                                        [unrolledReadSet],
                                        variables={"outdir": "{condition}/unrolled_reads_chunks"})
    return buildStmt.outputs


def genUnrolledMapping(pflow, unrolledReadSets, reference, splitFactor):
    # TODO here:
    # 1. chunking
    # 2. mapping
    unrolledBlasrOptions = "-hitPolicy leftmost -forwardOnly -fastSDP" # S3.1; future blasr moves to "--" POSIX style
    mapRule = pflow.genRuleOnce(
        "map_unrolled",
        "$gridSMP $ncpus pbalign --algorithmOptions=\\'%s\\' --nproc $ncpus $in $reference $out" % unrolledBlasrOptions)
    alignmentSets = []
    for unrolledReadSet in unrolledReadSets:
        with pflow.context("movieName", movieName(unrolledReadSet)):
            alignmentSetChunks = []
            unrolledReadSetChunks = genUnrolledReadSetSplit(pflow, unrolledReadSet, splitFactor)
            for (i, unrolledReadSetChunk) in enumerate(unrolledReadSetChunks):
                with pflow.context("chunkNum", i):
                    buildVariables = dict(reference=reference, ncpus=8)
                    buildStmt = pflow.genBuildStatement(
                        ["{condition}/unrolled_mapping_chunks/{movieName}.chunk{chunkNum}.unrolledalignmentset.xml"],
                        "map_unrolled",
                        [unrolledReadSetChunk],
                        buildVariables)
                    alignmentSetChunks.extend(buildStmt.outputs)
            alignmentSets.extend(
                genDatasetConsolidateForMovie(pflow, alignmentSetChunks, "unrolled_mapping", "unrolledalignmentset"))
    return genDatasetMergeForCondition(pflow, alignmentSets, "unrolled_mapping", "unrolledalignmentset")


# --

class UnrolledMappingWorkflow(Workflow):
    @staticmethod
    def name():
        return "UnrolledMapping"

    @staticmethod
    def conditionTableType():
        return UnrolledMappingConditionTable

    def generate(self, pflow, ct):
        outputDict = {}
        for condition in ct.conditions:
            with pflow.context("condition", condition):
                reference = ct.reference(condition)
                if ct.inputType == InputType.SubreadSet:
                    unrolledReads = genUnrolledReads(pflow, ct.inputs(condition))
                    outputDict[condition] = genUnrolledMapping(pflow, unrolledReads, reference, splitFactor=8)
                else:
                    raise NotImplementedError, "Support not yet implemented for this input type"
        return outputDict

class UnrolledNoHQMappingWorkfow(Workflow):
    @staticmethod
    def name():
        return "UnrolledNoHQMapping"


#
