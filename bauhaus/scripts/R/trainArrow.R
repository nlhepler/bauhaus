#!/usr/bin/env Rscript
## N.B. This requires R libraries that are installed in the module R/3.2.3-bauhaus

## Training script for Arrow consensus models.
## Steps:
##   1 - Loads a set of aligned BAM files
##   2 - Subsamples these to get small "windows" of alignments
##   3 - Creates an outcome variable for these alignments by encoding PW:BP as 1-12
##   4 - Removes grossly discordant data (read length nowhere near ref length)
##   5 - Fits  model using the hmm function
##   6 - Saves the fit for later use/investigation.
##   7 - Outputs cpp/json files ready to use with ConsensusCore2
##   8 - Outputs plots of transition/emission probabilities

## TODO: move "cpp" and "json" writers into the unitem library proper

suppressPackageStartupMessages({
    library(pbbamr)
    library(unitem)
    library(ggplot2)
    library(reshape2)
    library(scales)
    library(data.table)
    library(argparse)
    library(logging)
    library(jsonlite)
    library(nnet) ## Need this in order for coef(...$cfit) to work, should be fixed by moving into unitem
})

logging::basicConfig()

parser <- ArgumentParser()
parser$add_argument("alnFilesDir", nargs=1,
                    help="Directory containing alignmentsets and references (available as prefix.ref.fa")
## TODO(dalexander): fix restriction above
args <- parser$parse_args()


###### DEFINITIONS #######
use8Contexts    = F
zmwsPerBam      = 3000
targetAlnLength = 140

###### LOAD DATA ########
loginfo("Loading BAM indices")
alnFiles = Sys.glob(file.path(args$alnFilesDir, "*.alignmentset.xml"))
indexes = lapply(alnFiles, loadPBI)

## Sample the BAMs and trim, to get alignment windows of ~140 bp from
## each of 3000 ZMWs per BAM
getSamples <- function(i) {
  alnFile = alnFiles[[i]]
  loginfo("Loading samples from %s", alnFile)
  pbi = indexes[[i]]
  sampled_data = pbi[sample(nrow(pbi), min(nrow(pbi), zmwsPerBam)),]
  large_alns = loadAlnsFromIndex(sampled_data, paste(alnFile, ".ref.fa", sep=""))
  f_large_alns = Filter(function(x) nrow(x) > targetAlnLength, large_alns)
  small_alns = lapply(f_large_alns, function(x) trimAlignment(x, trimToLength = targetAlnLength))
  small_alns
}
alns = lapply(1:length(indexes), getSamples)
alns = unlist(alns, recursive = FALSE)


## Encode an outcome variable for the "Emmission" in the HMM model
mkOutcome <- function(aln) {
  aln <- subset(aln, select=c(read, ref, ipd, pw, snrA, snrC, snrG, snrT))
  # Remove dummy placeholders (no read for a ref position) to avoid making more than
  # 20 levels of the factor, these "Deletion" states will be removed anyway
  pw = aln$pw
  pw[pw == 0] = 1 # Template bases with no observation associated with them
  # Change PW to 1-3 encoding
  pw[pw > 3] = 3
  read = aln$read
  read[read == "-"] = "C" # Dummy value that overlaps with an actual factor, hack to avoid accounting for delete case
  # Generate the outcome factor
  aln$outcome = factor(pw, levels = c(1, 2, 3)):factor(read, levels = c("A", "C", "G", "T"))
  # Generate channel-specific SNR
  ctx = unitem::GenerateDinucleotideContextFromGappedRef(aln$ref, use8Contexts)
  snr = aln$snrA
  if (use8Contexts) {
    snr[ctx=="NC" | ctx=="CC"] = aln$snrC[1]
    snr[ctx=="NG" | ctx=="GG"] = aln$snrG[1]
    snr[ctx=="NT" | ctx=="TT"] = aln$snrT[1]
  } else {
    snr[ctx=="AC" | ctx=="CC" | ctx=="GC" | ctx=="TC"] = aln$snrC[1]
    snr[ctx=="AG" | ctx=="CG" | ctx=="GG" | ctx=="TG"] = aln$snrG[1]
    snr[ctx=="AT" | ctx=="CT" | ctx=="GT" | ctx=="TT"] = aln$snrT[1]
  }
  aln$snr = snr
  aln
}
loginfo("Encoding sample data")
training_data = lapply(alns, mkOutcome)


# Filter alignents where read/reference differ by more than 50%
filterData <- function(data) {
  isGood <- function(x) {
    nm = sum(x$read != "-")
    no = sum(x$ref != "-")
    diff = abs(1 - nm/no)
    diff < 0.5
  }
  Filter(isGood, data)
}
loginfo("Filtering highly discrepant alignments")
filt_training = filterData(training_data)

###### TRAIN MODEL #######
fit <- hmm(outcome ~ snr + I(snr^2) + I(snr^3), filt_training, filter = FALSE, end_dif = 1.5e-4, use8Contexts = use8Contexts)
print(fit)

### Clean the model to make for a smaller data file
cleanFit <- function(fit)
{
  fit$pseudoCounts = NULL
  fit$modelMatrix = NULL
  mdls = fit$models
  cleanModel <- function(mdl) {
    #mdl$cfit$fitted.values = NULL
    mdl$cfit$residuals = NULL
    #mdl$cfit$weights = NULL
    mdl$toUse = NULL
    attr(mdl$cfit$terms, ".Environment") <- NULL
    attr(mdl$cfit$terms, "dataClasses") <- NULL
    attr(mdl$cfit$terms, "predvars") <- NULL
    mdl
  }
  cleanmdls = lapply(mdls, cleanModel)
  #save(cleanmdls, file="context_models.rda")
  fit$models = cleanmdls
  fit
}
loginfo("Saving fit data")
fit.cleaned <- cleanFit(fit)
save(fit.cleaned, file="fit.rda", compress=TRUE)

# Get RANGE of SNR values fit for clamping
loginfo("Calculating SNR clamp range")
alns = data.frame(data.table::rbindlist(training_data))

qRange <- function(xs) { c(quantile(xs, 0.01), quantile(xs, 0.99)) }

snrRanges <- rbind(
    qRange(alns$snrA),
    qRange(alns$snrC),
    qRange(alns$snrG),
    qRange(alns$snrT))
#save(alns, file="alns.rda")
#save(snrRanges, file="snrs.rda")


#### OUTPUT MODEL ##########

loginfo("Outputting model to fit.cpp")

outputModelToCpp <- function(fit, fname)
{
  if (file.exists(fname)) file.remove(fname)

  outputEmissions <- function(fit, fname) {
    mats = list(list(m=fit$mPmf, n="matchPmf"),
                list(m=fit$bPmf, n="branchPmf"),
                list(m=fit$sPmf, n="stickPmf"))
    renderMatrix <- function(mat) {
        renderRow <- function(i) {
            paste("        {",
                  paste(formatC(mat$m[i,1:12], width=15, digits=9),
                        collapse=", "),
                  "}")
        }
        paste("    {// ", mat$n, "\n",
              paste(sapply(1:nrow(mat$m), renderRow), collapse=",\n"),
              "}",
              sep="")
    }
    val <- paste(
      "constexpr size_t OUTCOME_NUMBER = 12;\n",
      paste("constexpr size_t CONTEXT_NUMBER = ",nrow(fit$mPmf),";\n", sep=""),
      "constexpr double emissionPmf[3][CONTEXT_NUMBER][OUTCOME_NUMBER] = {\n",
      paste(sapply(mats, renderMatrix), collapse=",\n"),
      "};\n",
      sep="")
    write(val, file=fname, append=T)
  }

  outputTransitions <- function(fit, fname) {
    renderMatrix <- function(ctxFit, ctx) {
      cos = coef(ctxFit)
      renderRow <- function(x) {
          paste("        {",
                paste(formatC(cos[x,], width=15, digits=9), collapse=", "),
                "}")
      }
      paste(paste("    {// ", ctx, "\n", sep=""),
            paste(sapply(1:3, renderRow), collapse=",\n"),
            "}",
            sep="")
    }
    val <- paste(
      "constexpr double transProbs[CONTEXT_NUMBER][3][4] = {\n",
      paste(sapply(fit$models, function(m) renderMatrix(m$cfit, unitem:::fit.ctxs[m$ctx + 1])),
            collapse=",\n"),
                 "};\n",
                 sep="")
    write(val, file=fname, append=T)
  }

  outputEmissions(fit, fname)
  outputTransitions(fit, fname)
}
outputModelToCpp(fit, "fit.cpp")


### OUTPUT TO JSON FILE ###

loginfo("Outputting model to fit.json")

extractTransitionArray <- function(fit)
{
    extractTransitonMatrix <- function(cfit, ctx)
    {
        cos <- coef(cfit)
        names(cos) <- NULL
        unclass(cos)
    }
    array(data=lapply(fit$models,
                 function(m) extractTransitonMatrix(m$cfit, unitem:::fit.ctxs[m$ctx + 1])))

}

outputModelToJson <- function(fit, snrRanges)
{
  x <- list()
  x$ConsensusModelVersion  <- unbox("3.0.0")
  x$ChemistryName          <- unbox("trained_condition")
  x$ModelForm              <- unbox("PwSnr")
  x$SnrRanges              <- snrRanges
  x$EmissionParameters     <- array(data=as.array(list(
                                        fit$mPmf[,1:12],
                                        fit$bPmf[,1:12],
                                        fit$sPmf[,1:12])))
  x$TransmissionParameters <- extractTransitionArray(fit)
  x$CounterWeight          <- unbox(3.0)  # TODO: how do we get this right?
  jsonOut <- file("fit.json", "wt")
  cat(toJSON(x, digits=I(9), pretty=TRUE), file=jsonOut)
  close(jsonOut)
}

outputModelToJson(fit, snrRanges)

##### PLOT EMISSION, TRANSITION PROBABILITIES ###

loginfo("Plotting emission, transition probabilities")

plotEmissions <- function(fit, fname) {
  lvs  = rep(c(levels(training_data[[1]]$outcome), rep("N:N", 5)), 16)
  ctxs = c(sapply(unitem:::fit.ctxs, function(z) rep(z, 17)))
  mats = list(fit$mPmf, fit$bPmf, fit$sPmf)
  titles = c("Match", "Cognate Extra", "Non-Cognate Extra")
  titles = paste(titles, "State Emission Probabilites")
  pdf(fname, width=12, height=12)
  for(i in 1:3) {
    mat = mats[[i]]
    df = data.frame(outcome = lvs, ctx=ctxs, prob =as.vector(t(mat)))
    df$BP = sapply(as.character(df$outcome), function(x) strsplit(x, ":")[[1]][2])
    q = ggplot(df, aes(x=outcome,y=prob, fill=BP)) + geom_bar(stat="identity") + facet_wrap(~ctx) +
      theme_bw(base_size=10) + labs(x="PW:BP", y="Emission Probability", title=titles[i])
    print(q)
  }
  quiet <- capture.output(dev.off())
}
plotEmissions(fit, paste("Emissions.pdf"))


plotTransProbsFull <- function(fit, fname) {
  pdf(fname)
  for(i in 1:length(fit$models)) {
    cmodel = fit$models[[i]]$cfit
    tg = data.frame(cbind(predict(cmodel, type="probs")))
    colnames(tg) <- c("Match", "Branch", "Stick", "Delete")
    snr = model.matrix(cmodel)[,2]
    tg$SNR = snr
    ctx = unitem:::fit.ctxs[fit$models[[i]]$ctx + 1]
    tp = reshape2::melt(tg, id.vars = "SNR", value.name="rate", variable.name="Transition")
    v = ggplot(tp, aes(x=SNR, y =rate)) + geom_smooth(fill=NA) + facet_wrap(~Transition, scales="free") + labs(title=paste(ctx,"Rate Estimates")) + theme_bw() +
      scale_y_continuous(label=percent)
    print(v)
  }
  quiet <- capture.output(dev.off())
}
plotTransProbsFull(fit, "Transitions.pdf")


loginfo("Done!")
