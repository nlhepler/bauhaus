import os.path as op

def movieName(filename):
    """
    The movieName is reckoned as the first .-delimited part of the
    basename.

    (Filename is:

     dir/movieName[.chunkName].dsettype.xml    )
    """

    base = op.basename(filename)
    fields = base.split(".")
    assert len(fields) in (3, 4) and fields[-1] == "xml"
    movieName = fields[0]
    return movieName

def entityName(filename):
    """
    An entity is either a movie or a part (chunk) of a movie

    This is encoded in the filename as:

     dir/movieName[.chunkName].dsettype.xml
    """
    base = op.basename(filename)
    fields = base.split(".")
    assert len(fields) in (3, 4) and fields[-1] == "xml"
    return ".".join(fields[:-2])


# ------- Split/merge -------------


# Conventions (in the absence of types!):
#
#   - Every generator should returns the list of context-resolved
#     outputs from its final build statement
#

def genSubreadSetSplit(pflow, subreadSet, splitFactor):
    # Split by ZMWs.  Returns: [dset]
    assert splitFactor >= 1
    pflow.genRuleOnce(
            "splitByZmw",
            "$grid dataset split --zmws --chunks %d --outdir $outdir $in" % (splitFactor,))
    movie = movieName(subreadSet)
    splitOutputs =  [ "{condition}/subreads_chunks/%s.chunk%d.subreadset.xml" % (movie, i)
                      for i in xrange(splitFactor) ]
    buildStmt = pflow.genBuildStatement(splitOutputs,
                                        "splitByZmw",
                                        [subreadSet],
                                        variables={"outdir": "{condition}/subreads_chunks"})
    return buildStmt.outputs


# ---------

def genDatasetMergeForCondition(pflow, inputDatasets, taskTypeName, datasetTypeName):
    # Just merge datasets, for condition
    pflow.genRuleOnce("mergeDatasetsForCondition",
                      "$grid dataset merge $out $in")
    outputs = [ "{condition}/%s/all_movies.%s.xml" % (taskTypeName, datasetTypeName) ]
    buildStmtMerge = pflow.genBuildStatement(
        outputs,
        "mergeDatasetsForCondition",
        inputDatasets)
    return buildStmtMerge.outputs

def genDatasetConsolidateForMovie(pflow, datasets, taskTypeName, datasetTypeName):
    # 1) Merge datasets and 2) physically consolidate BAM files
    # 1.
    pflow.genRuleOnce("mergeDatasetsForMovie",
                      "$grid dataset merge $out $in")
    outputs = [ "{condition}/%s/{movieName}_preconsolidate.%s.xml" % \
                (taskTypeName, datasetTypeName) ]
    buildStmtMerge = pflow.genBuildStatement(
        outputs,
        "mergeDatasetsForMovie",
        datasets)
    mergedDataset = buildStmtMerge.outputs[0]
    # 2.
    pflow.genRuleOnce(
        "consolidateDatasetsForMovie",
        "$grid dataset consolidate $in $outBam $out")
    consolidatedDataset = "{condition}/%s/{movieName}.%s.xml" % (taskTypeName, datasetTypeName)
    # FIXME: this is gross.  Let's do something better.  For example,
    # we could have dataset subclasses that know how to perform
    # operations.
    if datasetTypeName == "alignmentset":
        bamTypeName = "aligned_subreads"
    elif datasetTypeName == "consensusreadset":
        bamTypeName = "ccs"
    else:
        raise Exception, "Unsupported dataset type..."
    consolidatedBam = "{condition}/%s/{movieName}.%s.bam" % (taskTypeName, bamTypeName)
    consolidatedDataset = "{condition}/%s/{movieName}.%s.xml" % (taskTypeName, datasetTypeName)
    buildStmtConsolidate = pflow.genBuildStatement(
        [consolidatedDataset],
        "consolidateDatasetsForMovie",
        [mergedDataset],
        dict(outBam=consolidatedBam))
    return buildStmtConsolidate.outputs
