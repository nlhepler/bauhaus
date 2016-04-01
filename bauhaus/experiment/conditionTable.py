__all__ = [ "InputType",
            "ConditionTable",
            "ResequencingConditionTable",
            "CoverageTitrationConditionTable",
            "conditionTableForWorkflow",
            "TableValidationError",
            "InputResolutionError" ]

import pandas
import os.path as op

class TableValidationError(Exception): pass
class InputResolutionError(Exception): pass

class _DfHelpers(object):
    @staticmethod
    def pVariables(df):
        return [ k for k in df.columns if k.startswith("p_") ]


class InputType(object):
    SubreadSet   = 1
    AlignmentSet = 2

class ConditionTable(object):
    """
    Base class for representing Milhouse-style condition tables

    Columns required: Condition, some encoding of input

    There is *no* column encoding secondary protocol; that's the way
    things work in Milhouse but not here.  The "protocol" is specified
    separately from the condition table, which is meant only to encode
    variables and their associated inputs.
    """
    def __init__(self, inputCsv, resolver):
        if not op.isfile(inputCsv):
            raise ValueError("Missing input file: %s" % inputCsv)
        try:
            self.df = pandas.read_csv(inputCsv)
        except:
            raise InputValidationError("Input CSV file can't be read/parsed")
        self._validateTable()
        self._resolveInputs(resolver)

    def _validateTable(self):
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
          - Varying covariate levels under a single condition name
        """
        self._validateConditionsAreHomogeneous()
        self._validateSingleInputEncoding()

    def _validateConditionsAreHomogeneous(self):
        for c in self.conditions:
            condition = self.condition(c)
            for variable in self.variables:
                if len(condition[variable].unique()) != 1:
                    raise TableValidationError(
                        "Conditions must be homogeneous---no variation in variables within a condition")

    def _validateSingleInputEncoding(self):
        cols = self.df.columns
        inputEncodings = 0
        if {"ReportsPath"}.issubset(cols):
            inputEncodings += 1
        if {"RunCode", "ReportsFolder"}.issubset(cols):
            inputEncodings += 1
        if {"RunCode", "ReportsFolderH5"}.issubset(cols):
            inputEncodings += 1
        if {"SMRTLinkServer", "JobId"}.issubset(cols):
            inputEncodings += 1
        if {"JobPath"}.issubset(cols):
            inputEncodings += 1
        if inputEncodings == 0:
            raise TableValidationError("Input data not encoded in condition table")
        if inputEncodings > 1:
            raise TableValidationError("Condition table can only represent input data in one way")

    def _resolveInput(self, resolver, rowRecord):
        cols = self.df.columns
        if {"ReportsPath"}.issubset(cols):
            raise NotImplementedError
        elif {"RunCode", "ReportsFolder"}.issubset(cols):
            # Is there a better way?  Maybe make resolvePrimaryPath recognize NaN?
            if pandas.isnull(rowRecord.ReportsFolder): reports = ""
            else: reports = rowRecord.ReportsFolder
            return resolver.resolveSubreadSet(rowRecord.RunCode, reports)
        elif {"RunCode", "ReportsFolderH5"}.issubset(cols):
            raise NotImplementedError
        elif {"SMRTLinkServer", "JobId"}.issubset(cols):
            return resolver.resolveAlignmentSet(rowRecord.SMRTLinkServer, rowRecord.JobId)
        elif {"JobPath"}.issubset(cols):
            raise NotImplementedError

    def _resolveInputs(self, resolver):
        self._inputsByCondition = {}
        for condition in self.conditions:
            subDf = self.condition(condition)
            inputs = []
            for row in subDf.to_records():
                inputs.append(self._resolveInput(resolver, row))
            self._inputsByCondition[condition] = inputs

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

    @property
    def inputType(self):
        cols = self.df.columns
        if {"ReportsPath"}.issubset(cols) or \
           {"RunCode", "ReportsFolder"}.issubset(cols):
            return InputType.SubreadSet
        if {"SMRTLinkServer", "JobId"}.issubset(cols) or \
           {"JobPath"}.issubset(cols):
            return InputType.AlignmentSet
        raise NotImplementedError, "Input type not recognized/supported"

    def inputs(self, condition):
        return self._inputsByCondition[condition]

class ResequencingConditionTable(ConditionTable):
    """
    Base class for representing Milhouse-style condition tables for
    resequencing-bases analyses (require a reference, use mapping)
    """
    def _validateGenomeColumnPresent(self):
        if "Genome" not in self.df.columns:
            raise InputValidationError("'Genome' column must be present")

    def _validateTable(self):
        """
        Additional validation: "Genome" column required
        """
        super(ResequencingConditionTable, self)._validateTable()
        self._validateGenomeColumnPresent()

    def _resolveInputs(self, resolver):
        super(ResequencingConditionTable, self)._resolveInputs(resolver)
        self._referenceByCondition = {}
        for condition in self.conditions:
            genome = self.genome(condition)
            self._referenceByCondition[condition] = resolver.resolveReference(genome)

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

    def reference(self, condition):
        return self._referenceByCondition[condition]


class CoverageTitrationConditionTable(ResequencingConditionTable):

    def _validateAtLeastOnePVariable(self):
        if len(_DfHelpers.pVariables(self.df)) < 1:
            raise InputValidationError(
                'There must be at least one covariate ("p_" variable) in the condition table')

    def _validateTable(self):
        super(CoverageTitrationConditionTable, self)._validateTable()
        #self._validateAtLeastOnePVariable()

    def referenceMask(self, condition):
        return self._referenceMaskByCondition[condition]

    def _resolveInputs(self, resolver):
        super(CoverageTitrationConditionTable, self)._resolveInputs(resolver)
        self._referenceMaskByCondition = {}
        for condition in self.conditions:
            genome = self.genome(condition)
            self._referenceMaskByCondition[condition] = resolver.resolveReferenceMask(genome)



def conditionTableForWorkflow(protocol, inputCsv, resolver):
    if protocol in [ "BasicMapping", "ChunkedMapping", "VariantCalling" ]:
        return ResequencingConditionTable(inputCsv, resolver)
    elif protocol in [ "CoverageTitration", "CoverageTitrationReports" ]:
        return CoverageTitrationConditionTable(inputCsv, resolver)
    else:
        raise NotImplementedError
