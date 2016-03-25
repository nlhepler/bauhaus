#!/bin/bash
source /mnt/software/Modules/current/init/bash
MODULEPATH=/pbi/dept/primary/modulefiles:$MODULEPATH

module purge
module load smrtanalysis/mainline
module load gfftools/dalexander
module load R/3.2.3-experimental

THISDIR=$(cd "$(dirname "$0")" && pwd)
cd $THISDIR
export PATH=$THISDIR/scripts:$PATH

~dalexander/bin/ninja
