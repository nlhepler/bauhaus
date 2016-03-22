from .mapping import genChunkedMappingWorkflow

# -- Basic variant calling...

def genVariantCalling(pflow, alignedSubreadsSet, reference,
                      referenceMask=None, algorithm="arrow", coverageLimit=None):
    """
    Run the variant calling algorithm with all variants filtering
    disabled, producing files:

     - variants{-coverageLimit}.gff
     - consensus{-coverageLimit}.fasta
     - consensus{-coverageLimit}.fastq

    TODO: do we like handling coverageLimit this way, or do we want to leverage PFLow context mechanism?
    """
    if coverageLimit is None:
        CONSENSUS_FASTA       = "{condition}/variant_calling/consensus.fasta"
        CONSENSUS_FASTQ       = "{condition}/variant_calling/consensus.fastq"
        VARIANTS_GFF          = "{condition}/variant_calling/variants.gff"
        MASKED_VARIANTS_GFF   = "{condition}/variant_calling/masked-variants.gff"
        coverageLimitArgument = ""
    else:
        CONSENSUS_FASTA       = "{condition}/variant_calling/consensus-%d.fasta"     % coverageLimit
        CONSENSUS_FASTQ       = "{condition}/variant_calling/consensus-%d.fastq"     % coverageLimit
        VARIANTS_GFF          = "{condition}/variant_calling/variants-%d.gff"        % coverageLimit
        MASKED_VARIANTS_GFF   = "{condition}/variant_calling/masked-variants-%d.gff" % coverageLimit
        coverageLimitArgument = "-X%d" % coverageLimit

    vcRule = pflow.genRuleOnce(
        "variantCalling",
        "$gridSMP $ncpus variantCaller --algorithm=%s $coverageLimitArgument -x0 -q0 -j $ncpus $in -r $reference -o $out -o $consensusFasta -o $consensusFastq"
        % (algorithm))

    bs = pflow.genBuildStatement(
        [VARIANTS_GFF],
        "variantCalling",
        [alignedSubreadsSet],
        dict(reference=reference,
             consensusFasta=CONSENSUS_FASTA,
             consensusFastq=CONSENSUS_FASTQ,
             coverageLimitArgument=coverageLimitArgument))

    if referenceMask is not None:
        maskRule = pflow.genRuleOnce(
            "maskVariantsGff",
            "gffsubtract.pl $in $referenceMask $out")
        # overwrite bs
        bs = pflow.genBuildStatement(
            [MASKED_VARIANTS_GFF], "maskVariantsGff", [VARIANTS_GFF],
            dict(referenceMask=referenceMask))

    return bs.outputs

def genCoverageSummary(pflow, alignmentSet, reference):
    pflow.genRuleOnce(
        "summarize_coverage",
        "$grid python -m pbreports.report.summarize_coverage.summarize_coverage $in $reference $out")
    bs = pflow.genBuildStatement(
        ["{condition}/variant_calling/alignments_summary.gff"],
        "summarize_coverage",
        [alignmentSet],
        dict(reference=reference))
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
            outputDict[condition] = genVariantCalling(pflow, alignmentSet, reference, algorithm="arrow")
    return outputDict
