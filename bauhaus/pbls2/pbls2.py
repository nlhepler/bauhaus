
__all__ = [ "Resolver",
            "MockResolver",
            "ResolverFailure",
            "DataNotFound" ]

import requests, json, os.path as op, re
from glob import glob
try:
    from urlparse import urlparse
except: # Py3K
    from urllib.parse import urlparse


class ResolverFailure(Exception): pass  # Internal failure in the resolver or nibbler
class DataNotFound(Exception):    pass  # Data not found in nibbler database


# We use the nibbler service to lookup run-codes until there is an
# alternative means.  We shouldn't use it to look up jobs.
def _nibble(query):
    r = requests.get("http://nibbler/" + query)
    if not r.ok:
        raise ResolverFailure("Nibbler failure: " + query)
    else:
        return json.loads(r.content.decode("UTF-8"))

def _isRuncode(runCode):
    return isinstance(runCode, str) and re.match("\d{7}-\d{4}", runCode)

def _isJobId(jobId):
    return isinstance(jobId, int)


class Resolver(object):
    """
    A `Resolver` object provides means to "resolve" identifiers to
    fully-qualified paths in PacBio NFS space.

    In particular, we can resolve: runcodes, secondary job
    identifiers, reference names (to the reference FASTA or the
    reference "mask")
    """

    # TODO: this isn't really hygienic because, in fact, there are
    # multiple reference repos, associated with different SL engines
    REFERENCE_MASKS_ROOT = "/mnt/secondary/Share/VariantCalling/Quiver/GenomeMasks"
    REFERENCES_ROOT = "/mnt/secondary/iSmrtanalysis/current/common/references"

    def __init__(self):
        self._selfCheck()

    def _selfCheck(self):
        """
        Test connectivity to the services behind the resolver
        """
        try:
            r = requests.get("http://nibbler")
            if not r.ok:
                raise ResolverFailure("Nibbler unavailable?")
        except requests.ConnectionError:
                raise ResolverFailure("Nibbler unavailable?")

        if not op.exists(self.REFERENCES_ROOT):
            raise ResolverFailure("NFS unavailable?")

    def resolveRunCode(self, runCode):
        """
        NFS path for run directory from runCode
        """
        if not _isRuncode(runCode):
            raise ValueError('Argument "%s" does not appear to be a runcode' % runCode)
        j = _nibble("collection?runcode=%s" % runCode)
        path = urlparse(j[0]["path"]).path
        if not path:
            raise DataNotFound(runCode)
        else:
            return path

    def resolvePrimaryPath(self, runCode, reportsFolder=""):
        """
        NFS path for run directory for reports directory from runCode and
        reportsFolder.
        """
        return op.join(self.resolveRunCode(runCode), reportsFolder)

    def resolveSubreadsSet(self, runCode, reportsFolder=""):
        reportsPath = self.resolvePrimaryPath(runCode, reportsFolder)
        subreadsFnames = glob(op.join(reportsPath, "*.subreadset.xml"))
        if len(subreadsFnames) < 1:
            raise DataNotFound("SubreadsSet not found in %s" % reportsPath)
        elif len(subreadsFnames) > 1:
            raise DataNotFound("Multiple SubreadsSets present: %s" % reportsPath)
        return subreadsFnames[0]

    def resolveReference(self, referenceName):
        referenceFasta = op.join(self.REFERENCES_ROOT, referenceName, "sequence", referenceName + ".fasta")
        if op.isfile(referenceFasta):
            return referenceFasta
        elif not op.exists(self.REFERENCES_ROOT):
            raise ResolverFailure("NFS unavailable?")
        else:
            raise DataNotFound(referenceName)

    def resolveReferenceMask(self, referenceName):
        maskGff = op.join(REFERENCES_MASKS_ROOT, referenceName + "-mask.gff")
        if op.isfile(maskGff):
            return maskGff
        elif not op.exists(REFERENCE_MASKS_ROOT):
            raise ResolverFailure("NFS unavailable?")
        else:
            raise DataNotFound("missing mask for " + referenceName)

    def resolveJob(self, smrtLinkServer, jobId):
        raise NotImplementedError

    def resolveReferenceForJob(self, smrtLinkServer, jobId):
        raise NotImplementedError

    def resolveAlignmentsSet(self, smrtLinkServer, jobId):
        raise NotImplementedError




class MockResolver(object):
    # For testing purposes

    def __init__(self):
        raise NotImplementedError
