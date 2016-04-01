
Let's try a very simple mapping job (no chunking)

  $ TABLE=$TESTDIR/../data/lambdaAndEcoli.csv

  $ bauhaus -o map -m -t $TABLE -w Mapping generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "map"


  $ tree map
  map
  |-- build.ninja
  |-- condition-table.csv
  |-- log
  `-- run.sh
  
  1 directory, 3 files


  $ cat map/condition-table.csv
  Condition,RunCode,ReportsFolder,Genome
  Lambda,3150128-0001,,lambdaNEB
  Lambda,3150128-0002,,lambdaNEB
  Ecoli,3150122-0001,,ecoliK12_pbi_March2013
  Ecoli,3150122-0002,,ecoliK12_pbi_March2013


  $ cat map/build.ninja
  # Variables
  ncpus = 8
  grid = qsub -sync y -cwd -V -b y -e log -o log
  gridSMP = $grid -pe smp
  
  # Rules
  rule map
    command = $gridSMP $ncpus pbalign --nproc $ncpus $in $reference $out
  
  rule mergeAlignmentSetsForCondition
    command = $grid dataset merge $out $in
  
  
  # Build targets
  build Lambda/mapping/m54008_160308_002050.alignmentset.xml: map $
      /pbi/collections/315/3150128/r54008_20160308_001811/1_A01/m54008_160308_002050.subreadset.xml
    ncpus = 8
    reference = $
        /mnt/secondary/iSmrtanalysis/current/common/references/lambdaNEB/sequence/lambdaNEB.fasta
  
  build Lambda/mapping/m54008_160308_053311.alignmentset.xml: map $
      /pbi/collections/315/3150128/r54008_20160308_001811/2_B01/m54008_160308_053311.subreadset.xml
    ncpus = 8
    reference = $
        /mnt/secondary/iSmrtanalysis/current/common/references/lambdaNEB/sequence/lambdaNEB.fasta
  
  build Lambda/mapping/all_movies.alignmentset.xml: $
      mergeAlignmentSetsForCondition $
      Lambda/mapping/m54008_160308_002050.alignmentset.xml $
      Lambda/mapping/m54008_160308_053311.alignmentset.xml
  
  build Ecoli/mapping/m54011_160305_235923.alignmentset.xml: map $
      /pbi/collections/315/3150122/r54011_20160305_235615/1_A01/m54011_160305_235923.subreadset.xml
    ncpus = 8
    reference = $
        /mnt/secondary/iSmrtanalysis/current/common/references/ecoliK12_pbi_March2013/sequence/ecoliK12_pbi_March2013.fasta
  
  build Ecoli/mapping/m54011_160306_050740.alignmentset.xml: map $
      /pbi/collections/315/3150122/r54011_20160305_235615/2_B01/m54011_160306_050740.subreadset.xml
    ncpus = 8
    reference = $
        /mnt/secondary/iSmrtanalysis/current/common/references/ecoliK12_pbi_March2013/sequence/ecoliK12_pbi_March2013.fasta
  
  build Ecoli/mapping/all_movies.alignmentset.xml: $
      mergeAlignmentSetsForCondition $
      Ecoli/mapping/m54011_160305_235923.alignmentset.xml $
      Ecoli/mapping/m54011_160306_050740.alignmentset.xml
  


















