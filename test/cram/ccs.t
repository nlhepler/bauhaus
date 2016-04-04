
  $ TABLE=$TESTDIR/../data/lambdaAndEcoli.csv

  $ bauhaus -o ccs -m -t $TABLE -w BasicCCS generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "ccs"


  $ bauhaus -o chunkedCCS -m -t $TABLE -w ChunkedCCS generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "chunkedCCS"


  $ bauhaus -o ccsMap -m -t $TABLE -w CCSMapping generate
  Validation and input resolution succeeded.
  Runnable workflow written to directory "ccsMap"
