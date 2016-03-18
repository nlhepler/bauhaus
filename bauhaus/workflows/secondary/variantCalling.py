from .mapping import genChunkedMappingWorkflow

# -- Basic variant calling...

def genUnfilteredVariantCalling(pflow, alignedSubreadsSet, reference, algorithm="arrow", coverageLimit=None):
    """
    Run the variant calling algorithm with all variants filtering
    disabled, producing files:

     - variants{-coverageLimit}.gff
     - consensus{-coverageLimit}.fasta
     - consensus{-coverageLimit}.fastq

    TODO: do we like handling coverageLimit this way, or do we want to leverage PFLow context mechanism?
    """
    if coverageLimit is None:
        CONSENSUS_FASTA = "{condition}/variant_calling/consensus.fasta"
        CONSENSUS_FASTQ = "{condition}/variant_calling/consensus.fastq"
        VARIANTS_GFF    = "{condition}/variant_calling/variants.gff"
        coverageLimitArgument = ""
    else:
        CONSENSUS_FASTA = "{condition}/variant_calling/consensus-%d.fasta" % coverageLimit
        CONSENSUS_FASTQ = "{condition}/variant_calling/consensus-%d.fastq" % coverageLimit
        VARIANTS_GFF    = "{condition}/variant_calling/variants-%d.gff"    % coverageLimit
        coverageLimitArgument = "-X%d" % coverageLimit

    vcRule = pflow.genRuleOnce(
        "variantCalling",
        "$gridSMP $ncpus variantCaller --algorithm=%s $coverageLimitArgument -x0 -q0 -j $ncpus $in -r $reference -o $out -o $consensusFasta -o $consensusFastq"
        % (algorithm))
    bs = pflow.genBuildStatement(
        [VARIANTS_GFF],
        "variantCalling",
        [alignedSubreadsSet],
        dict(consensusFasta=CONSENSUS_FASTA,
             consensusFastq=CONSENSUS_FASTQ,
             coverageLimitArgument=coverageLimitArgument))
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
