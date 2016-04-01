import argparse, shutil, sys, os, os.path as op

from bauhaus.experiment import conditionTableForWorkflow
from bauhaus.pbls2 import Resolver, MockResolver
from bauhaus.pflow import PFlow
from bauhaus.workflows import availableWorkflows
from bauhaus.utils import mkdirp

def doValidate(args):
    if args.mockResolver:
        r = MockResolver()
    else:
        r = Resolver()
    ct = conditionTableForWorkflow(args.workflow, args.conditionTable, r)
    print "Validation and input resolution succeeded."
    return ct

def doGenerate(args):
    ct = doValidate(args)
    gen = availableWorkflows[args.workflow]
    pflow = PFlow()
    gen(pflow, ct)
    pflow.write("build.ninja")
    print 'Runnable workflow written to directory "%s"' % args.outputDirectory

def doRun(args):
    raise NotImplementedError

def parseArgs():
    parser = argparse.ArgumentParser(prog="bauhaus")
    parser.add_argument(
        "--conditionTable", "-t",
        action="store", metavar="CONDITION_TABLE.CSV",
        required=True,
        type=op.abspath)
    parser.add_argument(
        "--workflow", "-w",
        action="store", type=str,
        required=True,
        choices = availableWorkflows.keys())
    parser.add_argument(
        "--mockResolver", "-m",
        action="store_true",
        help="Use mock pbls2 resolver (for testing purposes)")
    parser.add_argument(
        "--pdb", action="store_true",
        help="Drop into debugger on exception")
    parser.add_argument(
        "--outputDirectory", "-o",
        default="out",
        action="store", type=str)

    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    validate = subparsers.add_parser("validate", help="Validate the condition table")
    generate = subparsers.add_parser("generate", help="Generate the ninja script to run the workflow")
    run = subparsers.add_parser("run", help="Run the workflow")

    args = parser.parse_args()
    return args


def _main(args):
    #print args

    if args.command == "validate":
        doValidate(args)
        return

    mkdirp(args.outputDirectory)
    shutil.copyfile(args.conditionTable, op.join(args.outputDirectory, "condition-table.csv"))
    os.chdir(args.outputDirectory)
    mkdirp("log")


    if args.command == "generate":
        doGenerate(args)
    elif args.command == "run":
        doRun(args)


def main():
    args = parseArgs()
    if args.pdb:
        try:
            import ipdb
            with ipdb.launch_ipdb_on_exception():
                _main(args)
            return 0
        except ImportError:
            _main(args)
    else:
        _main(args)


if __name__ == '__main__':
    main()
