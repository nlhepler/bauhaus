
  ![bauhaus logo](./doc/img/bauhaus.png)

  [![Circle CI](https://circleci.com/gh/dalexander/bauhaus/tree/ci.svg?style=svg)](https://circleci.com/gh/dalexander/bauhaus/tree/ci)

   `bauhaus` is a prototype implementation of a minimal
   tertiary-analysis system for use in-house at PacBio.  It is not
   intended as an official solution, but more as an experimental
   playground for some ideas about how users can specify input and
   analyis conditions.

   `bauhaus` is best understood as a *compiler*.  It accepts the
   user's specification of the experiment (a CSV table with a
   [well-defined schema][condition-table-spec]), validates the table,
   resolves the inputs (which can be referred to symbolically using
   *runcodes*, or *job identifiers*, or explicitly using paths), and
   then generates an output directory containing files `run.sh` and
   `build.ninja`.  `build.ninja` is a jobscript runnable using the
   ["ninja" build tool][ninja]; `run.sh` is the main entry point,
   which sets up the software environment properly and then executes
   the Ninja script.

## How to get started?

   Please read the [tutorial](./doc/TUTORIAL.md).

## Usage manual

   To run a *workflow*, with inputs and variables specified by a
   *condition table*, you can invoke the `run` subcommand:

   ```sh
   % bauhaus -o myWorkflow -w {workFlowName} -t condition-table.csv run
   ```

   This command does a few things: it 1) validates that the condition
   table honors the schema and refers to valid input; 2) it compiles
   the ninja script for the workflow and copies it and other required
   scripts to the output directory ("myWorkflow" here); 3) it executes
   the workflow.

   You can also run the validate and generate steps without running
   the workflow.  The `generate` subcommand performs validation and
   generates the workflow directory, ready for execution.

   ```sh
   % bauhaus -o myWorkflow  -w {workFlowName} -t condition-table.csv generate
   ```

   The `validate` subcommand performs just the validation.

   ```sh
   % bauhaus -w {workFlowName} -t condition-table.csv validate
   ```


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
     separate, robust, tool.  However, it lacks dynamic
     capabilities, and the `ninja` buidld

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


[ninja]: http://ninja-build.org/
[condition-table-spec]: ./doc/ConditionTableSpec.org
