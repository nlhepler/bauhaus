from .mapping import genChunkedMappingWorkflow

# -- Basic variant calling...

def genUnfilteredVariantCalling(pflow, alignedSubreadsSet, reference, algorithm,
                                coverageLimit=None, contextSuffix=""):
    """
    Run the variant calling algorithm with all variants filtering
    disabled, producing files:

     - variants{-suffix}.gff
     - consensus{-suffix}.fasta
     - consensus{-suffix}.fastq
    """
    vcRule = pflow.genRuleOnce(
        "variantCalling",
        "$gridSMP $ncpus variantCaller -x0 -q0 -j $ncpus $in -r $reference -o $out -o $consensusFasta -o $consensusFastq")
    bs = pflow.genBuildStatement(
        ["{condition}/variant_calling/variants.gff"],
        "variantCalling",
        [alignedSubreadsSet],
        dict(consensusFasta="{condition}/variant_calling/consensus.fasta",
             consensusFastq="{condition}/variant_calling/consensus.fastq"))
    return bs.outputs


def genVariantCallingWorkflow(pflow, ct):
    """
    Run variant calling on every condition.
    """
    mapping = genChunkedMappingWorkflow(pflow, ct)
    outputDict = {}
    for (condition, alignmentSets) in mapping.iteritems():
        alignmentSet = alignmentSets[0]
        reference = ct.reference(condition)
        with pflow.context("condition", condition):
            outputDict[condition] = genUnfilteredVariantCalling(pflow, alignmentSet, reference, algorithm="arrow")
    return outputDict
