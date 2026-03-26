import subprocess
import islpy as isl
from fractions import Fraction

# TODO this may be improved later by having a single process instead of making a new process all the time!
def barvinok_sum_pwqp(pwqpoly: isl.PwQPolynomial) -> Fraction:
    string_representation = "[] -> " + str(pwqpoly)
    result = subprocess.run(
        ["/home/ivo/Documents/barvinok/barvinok_summate"],
        input=string_representation.encode(),
        capture_output=True,
        check=True
    )
    res = Fraction(result.stdout.decode().strip().strip("{} "))
    return res