
# bauhaus: a simplistic tertiary-analysis system for PacBio


## What is this?


## What does it consist of?

   - `experiment` subpackage: A model and API for the `condition table`
     that is provided by the user as a specification of the input
     data, grouped by "conditions" with associated experimental
     variables.  This model includes a specification; the API
     *validates* the condition table, enabling quick feedback on
     problems in experiment setup.  This feature was lacking in the
     original Milhouse system.

   - `pbls2` subpackage: An API for resolving internal-PacBio input
     data specifiers (runcodes, job IDs) to concrete NFS paths to
     dataset objects.

   - `pflow` subpackage: a minimal, experimental workflow engine I
     wrote just as a lark.  It takes a different approach than other
     engines---running `pflow` just generates a `ninja` build file
     that then can be invoked to execute the workflow.  There are
     advantages to this approach: it enables workflows to be composed
     in a language (Python) that has genuine capabilities for
     composability, and then leaves execution to be driven by a
     separate, robust, tool.  However, it lacks any dynamic
     capabilities.

   - `workflows` subpackage: workflows building on the `pflow` engine
     and the `experiment` model.  The workflows are divided into
     `secondary` and `tertiary` analyses.  The distinction is that
     `secondary` workflows treat input conditions independently, just
     shepherding a condition through mapping, variant calling, etc.
     `tertiary` workflows build on `secondary` workflows, and then
     perform a metanalysis, comparing conditions and generating plots
     and tables.


## Plans

  The following subpackages will be spun out into their own python packages:
      - `pbls2`
      - `experiment` (as `pbexperiment`)

  The `pflow` workflow engine is just a lark and is not intended to be
  used for the "real" tertiary analysis system.  For that, we are
  going to leverage `pbsmrtpipe`.
