__all__ = [ "ResolverFailure",
            "DataNotFound" ]

class ResolverFailure(Exception): pass  # Internal failure in the resolver or nibbler
class DataNotFound(Exception):    pass  # Data not found in nibbler database
