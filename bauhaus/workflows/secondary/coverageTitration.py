from .variantCalling import genVariantCalling, genCoverageSummary
from .mapping import genChunkedMappingWorkflow

from collections import defaultdict

COVERAGE_LEVELS = [5, 10, 15, 20, 30, 40, 50, 60, 80, 100]

def genCoverageTitrationWorkflow(pflow, ct, algorithm="arrow"):
    """
    TODO: do we want to make algorithm pick up on a column in the
          table? P_ConsensusAlgorithm
    """
    pflow.bundleScript("R/coverageTitrationPlots.R")

    mapping = genChunkedMappingWorkflow(pflow, ct)
    outputDict = defaultdict(list)
    for (condition, alignmentSets) in mapping.iteritems():
        alignmentSet = alignmentSets[0]
        reference = ct.reference(condition)
        referenceMask = ct.referenceMask(condition)
        with pflow.context("condition", condition):
            coverageSummary = genCoverageSummary(pflow, alignmentSet, reference)[0]
            outputDict[condition].append(coverageSummary)
            for x in COVERAGE_LEVELS:
                outputDict[condition].append(
                    genVariantCalling(pflow, alignmentSet, reference,
                                      referenceMask=referenceMask,
                                      algorithm=algorithm,
                                      coverageLimit=x))
    return outputDict
