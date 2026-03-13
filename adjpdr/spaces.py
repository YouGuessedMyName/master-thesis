"""Functions that are used in the conflict heuristic that involve solution spaces for linear equations."""

def generator_set_cdd(r, r0):
    """Get the explicit generator set using cdd, for the set { v : r*v <= r0}."""
    pass

def generator_set(r, r0):
    """Get the explicit generator set using our own implementation, for the set { v : r*v <= r0}."""
    pass

def generator_set_meet(r, r0, v):
    """Get the meet of Zk = { d : generator_set(r, r0) | v <= d}."""
    pass