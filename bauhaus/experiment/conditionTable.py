__all__ = [ "ConditionTable", "ResequencingConditionTable" ]

import pandas
import os.path as op
from genomes import GENOMES

class InputValidationError(Exception): pass

class _DfHelpers(object):
    @staticmethod
    def pVariables(df):
        return [ k for k in df.columns if k.startswith("p_") ]


class ConditionTable(object):
    """
    Base class for representing Milhouse-style condition tables

    Columns required: Condition, some encoding of input

    There is *no* column encoding secondary protocol; that's the way
    things work in Milhouse but not here.  The "protocol" is specified
    separately from the condition table, which is meant only to encode
    variables and their associated inputs.
    """
    def __init__(self, inputCsv):
        if not op.isfile(inputCsv):
            raise ValueError("Missing input file: %s" % inputCsv)
        try:
            self.df = pandas.read_csv(inputCsv)
        except:
            raise InputValidationError("Input CSV file can't be read/parsed")
        self.validateInput()

    def validateInput(self):
        """
        Validate the input CSV file
        Exception on invalid input.

        The intention here is that this can quickly run (by a local
        "validate" rule) to spot errors in the input CSV, before we
        attempt to run the workflow.

        Possible errors that are checked for:
          - Malformed CSV input (can't be parsed)
          - Incorrect header row
          - Too few/many p_ conditions
          - Run folder doesn't exist or is inaccessible
          - Varying covariate levels under a single condition name
        """
        self._validateConditionsAreHomogeneous()

    def _validateConditionsAreHomogeneous(self):
        for c in self.conditions:
            condition = self.condition(c)
            for variable in self.variables:
                if len(condition[variable].unique()) != 1:
                    raise InputValidationError("Conditions must be homogeneous---no variation in variables within a condition")

    @property
    def conditions(self):
        return self.df.Condition.unique()

    def condition(self, condition):
        # Get subtable for condition
        return self.df[self.df.Condition == condition]

    @property
    def pVariables(self):
        """
        "p variables" encoded in the condition table using column names "p_*"
        """
        return _DfHelpers.pVariables(self.df)

    @property
    def variables(self):
        """
        "Covariates" are the "p_" variables           -
        """
        return self.pVariables

    def variable(self, condition, variableName):
        """
        Get the value of a variable within a condition
        """
        vals = self.condition(condition)[variableName].unique()
        assert len(vals) == 1
        return vals[0]


class ResequencingConditionTable(ConditionTable):
    """
    Base class for representing Milhouse-style condition tables for
    resequencing-bases analyses (require a reference, use mapping)
    """
    def _validateGenomeColumnPresent(self):
        if "Genome" not in self.df.columns:
            raise InputValidationError("'Genome' column must be present")

    def validateInput(self):
        """
        Additional validation: "Genome" column required
        """
        super().validateInput()
        self._validateGenomeColumnPresent()

    @property
    def variables(self):
        """
        In addition to the "p_" variables, "Genome" is considered an implicit
        variable in resequencing experiments
        """
        return [ "Genome" ] + self.pVariables


    def genome(self, condition):
        """
        Use the condition table to look up the correct "Genome" based on
        the condition name
        """
        genomes = self.condition(condition).Genome.unique()
        assert len(genomes) == 1
        return genomes[0]


class CoverageTitrationConditionTable(ResequencingConditionTable):
    """
    `CoverageTitrationConditionTable` requires "Genome" values to be
    recognized from a short list
    """
    def _validateNoUnrecognizedGenomes(self):
        unrecognizedGenomes = set(self.df.Genome).difference(GENOMES)
        if unrecognizedGenomes:
            raise InputValidationError("Unsupported genome(s) for this protocol: " +
                                       ", ".join(g for g in unrecognizedGenomes))

    def _validateAtLeastOnePVariable(self):
        if len(_DfHelpers.pVariables(self.df)) < 1:
            raise InputValidationError(
                'There must be at least one covariate ("p_" variable) in the condition table')


    def validateInput(self):
        super().validateInput()
        self._validateNoUnrecognizedGenomes()
        self._validateAtLeastOnePVariable()
