import os.path as op

def movieName(filename):
    base = op.basename(filename)
    fields = base.split(".")
    assert len(fields) in (3, 4) and fields[-1] == "xml"
    movieName = fields[0]
    return movieName

# ------- Split/merge -------------


# Conventions (in the absence of types!):
#
#   - Every generator should returns the list of context-resolved
#     outputs from its final build statement
#

def genSubreadsSetSplit(pflow, subreadsSet, splitFactor):
    # Split by ZMWs.  Returns: [dset]
    assert splitFactor >= 1
    pflow.genRuleOnce(
            "splitByZmw",
            "$grid dataset split --zmws --chunks %d --outdir $outdir $in" % (splitFactor,))
    movie = movieName(subreadsSet)
    splitOutputs =  [ "{condition}/subreads_chunks/%s.chunk%d.subreadset.xml" % (movie, i)
                      for i in xrange(splitFactor) ]
    buildStmt = pflow.genBuildStatement(splitOutputs,
                                        "splitByZmw",
                                        [subreadsSet],
                                        variables={"outdir": "{condition}/subreads_chunks"})
    return buildStmt.outputs


def genAlignmentSetConsolidateForMovie(pflow, alignmentSets):
    # CONSOLIDATE entails actually merging BAM files
    # We first need to run a MERGE.
    pflow.genRuleOnce("mergeAlignmentSetsForMovie",
                      "$grid dataset merge $out $in")
    outputs = [ "{condition}/mapping/{movieName}_preconsolidate.alignmentset.xml" ]
    buildStmtMerge = pflow.genBuildStatement(outputs,
                                        "mergeAlignmentSetsForMovie",
                                        alignmentSets)

    mergedAlignmentSet = buildStmtMerge.outputs[0]
    pflow.genRuleOnce("consolidateAlignmentSetsForMovie",
                      "$grid dataset consolidate $in $out")
    consolidateAlignmentSet = "{condition}/mapping/{movieName}.alignmentset.xml"
    consolidatedBam = "{condition}/mapping/{movieName}.aligned_subreads.bam"
    outputs = [ consolidatedBam, consolidateAlignmentSet ]
    buildStmtConsolidate = pflow.genBuildStatement(outputs,
                                                   "consolidateAlignmentSetsForMovie",
                                                   [mergedAlignmentSet])
    return [ buildStmtConsolidate.outputs[1] ]


def genAlignmentSetMergeForCondition(pflow, alignmentSets):
    pflow.genRuleOnce("mergeAlignmentSetsForCondition",
                      "$grid dataset merge $out $in")
    outputs = [ "{condition}/mapping/all_movies.alignmentset.xml" ]
    buildStmtMerge = pflow.genBuildStatement(outputs,
                                             "mergeAlignmentSetsForCondition",
                                             alignmentSets)
    return buildStmtMerge.outputs
