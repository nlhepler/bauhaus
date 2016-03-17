import argparse

def main():
    parser = argparse.ArgumentParser(prog="bauhaus")
    parser.add_argument(
        "--conditionTable", "-t",
        action="store", metavar="CONDITION_TABLE.CSV",
        required=True,
        type=str)
    parser.add_argument(
        "--protocol", "-p",
        action="store", type=str,
        required=True,
        choices = ["Mapping", "ChunkedMapping"])

    subparsers = parser.add_subparsers(help="sub-command help")
    validate = subparsers.add_parser("validate", help="Validate the condition table")
    generate = subparsers.add_parser("generate", help="Generate the ninja script to run the workflow")
    run = subparsers.add_parser("run", help="Run the workflow")

    args = parser.parse_args()
    print args

if __name__ == '__main__':
    main()
