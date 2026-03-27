import islpy as isl
from sym_adjpdr.barvinok_bindings import BarvinokSummator

# Create your piecewise quasi-polynomial
pwqpoly = isl.PwQPolynomial("{ [x] -> 6 * x : 0 <= x <= 3; [x] -> 18 : 4 <= x <= 5 }") # your polynomial here

# Persistent summator
summator = BarvinokSummator()

try:
    result = summator.sum_pwqp(pwqpoly)
    print("Sum =", result)
finally:
    summator.close()