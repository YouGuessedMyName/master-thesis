import subprocess
import islpy as isl
from fractions import Fraction

# TODO this may be improved later by having a single process instead of making a new process all the time!
# I could potentially improve this by editing barvinok_summate by adding a single while loop and then only having one process
# Nice-to-have feature? Or it could even be really required for reasonable performance, who knows?
def barvinok_sum_pwqp(pwqpoly: isl.PwQPolynomial) -> Fraction:
    string_representation = "[] -> " + str(pwqpoly)
    result = subprocess.run(
        ["/home/ivo/Documents/barvinok/.libs/barvinok_summate"],
        input=string_representation.encode(),
        capture_output=True,
        check=True
    )
    res = Fraction(result.stdout.decode().strip().strip("{} "))
    return res