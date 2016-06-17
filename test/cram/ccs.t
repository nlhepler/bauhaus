  $ BH_ROOT=$TESTDIR/../../

  $ bauhaus -o ccs -m -t ${BH_ROOT}test//data/lambdaAndEcoli.csv -w BasicCCS generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "ccs"


  $ bauhaus -o chunkedCCS -m -t ${BH_ROOT}test/data/lambdaAndEcoli.csv -w ChunkedCCS generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "chunkedCCS"


  $ bauhaus -o ccsMap -m -t ${BH_ROOT}test/data/lambdaAndEcoli.csv -w CCSMapping generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "ccsMap"
