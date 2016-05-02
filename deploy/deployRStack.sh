#!/bin/bash
. /mnt/software/Modules/current/init/bash
module add R/3.2.3-bauhaus
Rscript ./deployRStack.R
