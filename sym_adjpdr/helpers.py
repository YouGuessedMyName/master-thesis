from adjpdr.helpers import Frac
import z3

type State = list[tuple[z3.Int, int]]

class Frame:
    """Conceptually, a frame is a function from States to values in [0,1].
    Internally, this is a list of tuples which represent a piecewise function."""
    frame: list[tuple[z3.ArithRef, Frac]]

    def f():
        