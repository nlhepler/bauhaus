library(ggplot2)
library(plyr)
library(stringr)
library(pbutils)
library(gtools) # for "permutations"

ignore <- function(x) {}

doTitrationPlots <- function(tbl)
{
    tbl <- tbl[tbl$ShouldCensor=="False",]

    ## Implicit variables: Genome, Algorithm
    ## Explicit variables: have the "p_" prefix
    variables <- names(tbl)[grep("^p_|^Genome$|^Algorithm$", names(tbl))]
    stopifnot(length(variables) %in% c(1,2,3,4))

    print(ggplot(tbl, aes(x=Coverage, y=ConcordanceQV, color=Condition:Algorithm)) +
          geom_line() +
          scale_y_continuous("Concordance (QV)") +
          #scale_color_manual(values = extras$colors) +
          ggtitle("Consensus Performance, all conditions"))
  
    # Facet on individual variables
    for (v in variables) {
        print(
            ggplot(tbl, aes(x=Coverage, y=ConcordanceQV, color=Condition:Algorithm)) +
            geom_line() +
            facet_grid(paste(".~", v)) +
            scale_y_continuous("Concordance (QV)") +
            #scale_color_manual(values = extras$colors) +
            ggtitle(paste("Consensus Performance By", v)))
    }

    if (length(variables) >= 2)
    {
      # Take pairs of variables, facet on first and color by second
      apply(permutations(n=length(variables), r=2, v=variables), 1,
            function(twoVars)
            {
              ignore <- print(
                ggplot(tbl, aes_string(x="Coverage", y="ConcordanceQV", color=twoVars[2], group="Condition:Algorithm")) +
                  geom_line() +
                  facet_grid(paste(".~", twoVars[1])) +
                  scale_y_continuous("Concordance (QV)") +
                  #scale_color_manual(values = extras$colors) +
                  ggtitle(paste("Consensus Performance By", twoVars[1])))
            })
    }
    
    # Take triples of variables, facet on first two and color by third
    if (length(variables) >= 3)
    {
      # Take pairs of variables, facet on first and color by second
      apply(permutations(n=length(variables), r=3, v=variables), 1,
            function(twoVars)
            {
              print(
                ggplot(tbl, aes_string(x="Coverage", y="ConcordanceQV", color=twoVars[3], group="Condition:Algorithm")) +
                  geom_line() +
                  facet_grid(paste(twoVars[1], "~", twoVars[2])) +
                  scale_y_continuous("Concordance (QV)") +
                  #scale_color_manual(values = extras$colors) +
                  ggtitle(paste0("Consensus Performance By ", twoVars[1], ", ", twoVars[2])))
            })
    }
}


doCoverageDiagnosticsPlot <- function(tbl)
{
    ## Diagnostic plot of coverage
    print(qplot(Condition, AvailableCoverage, data=tbl, color=Condition) +
          theme(axis.text.x = element_text(angle=90, hjust=1)) +
          geom_hline(yintercept=80, col="red") +
          ggtitle("1-percentile coverage level by Condition"))
}

doResidualErrorsPlot <- function(tbl)
{
    ## Plots of residual error modes
    tbl <- tbl[tbl$ShouldCensor=="False",]

    summarizedResidualErrors <- function(variantsGffFile) {
        print(variantsGffFile)
        gff <- readGFF(variantsGffFile)
        if (nrow(gff) > 0) {
            base <- ifelse(gff$reference == ".", gff$variantSeq, gff$reference)
            base <- str_sub(base, 1, 1)
            ##count(interaction(gff$type, base))
            df <- as.data.frame(table(interaction(base, gff$type)))
            df$Base      <- str_sub(df$Var1, 1, 1)
            df$ErrorMode <- str_sub(df$Var1, 3)
            df
        }
    }

    #MIN.COVERAGE <- 40
    ROUND.COVERAGE <- c(40, 60, 100)
    variables <- names(tbl)[grep("^p_", names(tbl))]
    
    for (algorithm in levels(tbl$Algorithm))
    {
      varTypeCounts <- ddply(subset(tbl, Coverage %in% ROUND.COVERAGE & Algorithm==algorithm),
                             append(c("Condition", "Algorithm", "Coverage", "MaskedVariantsFile", "Genome"), variables),
                             function(df) {
                                res <- summarizedResidualErrors(as.character(df$MaskedVariantsFile))
                             })
  
      plt <- qplot(ErrorMode, Freq, geom="bar", stat="identity", fill=Base, data=varTypeCounts)
      facet.formula <- as.formula(paste(paste(variables, collapse="*"), "~Genome*Coverage"))
      plt.fix_y  <- (plt + facet_grid(facet.formula) 
                     +  ggtitle(sprintf("Residual errors in %s consensus sequence (fixed y-axis)", algorithm)))
      plt.free_y <- (plt + facet_grid(facet.formula, scale="free_y") 
                     + ggtitle(sprintf("Residual errors in %s consensus sequence (free y-axis)", algorithm)))
  
      print(plt.fix_y)
      print(plt.free_y)
    }
}

grok <- function(tbl)
{
    ## HACKY
    ## Grok the SNR into factor levels.

    ## If there is an SNR variable, assume the format <min>-<max> for each.
    ## Long-term would be nice to have the extra params as an actual class
    ## object with some notion of the type of param it is.
    variables <- names(tbl)[grep("^p_", names(tbl))]
    varsSNR <- variables[grep("*[sS][nN][rR]*", variables)]
    for (v in varsSNR) {
        snrRange <- str_extract_all(tbl[,v], "[0-9]+")
        minSNR <- min(as.numeric(unlist(snrRange)))
        maxSNR <- max(as.numeric(unlist(snrRange)))
        interSNR <- sapply(snrRange, function(s) {
            minV <- min(as.numeric(s))
            minV + 0.1
        })
        snrCuts <- cut(interSNR, breaks=sort(unique(as.numeric(unlist(snrRange)))))
        tbl[,v] <- snrCuts
    }
    tbl
}

main <- function()
{
    args <- commandArgs(TRUE)
    tbl <- grok(read.csv(args[1]))
    #tbl <- grok(read.csv("summary.csv"))
    
    #print(tbl)

    pdf("summary.pdf", 11, 8.5)
    doTitrationPlots(tbl)
    doCoverageDiagnosticsPlot(tbl)
    doResidualErrorsPlot(tbl)
}


main()
