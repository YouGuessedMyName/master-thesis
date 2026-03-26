import ctypes
import ctypes.util
import islpy as isl

BARVINOK_PATH = "/opt/barvinok/lib/libbarvinok.so"
lib = ctypes.CDLL(BARVINOK_PATH)

# Function signatures
lib.isl_pw_qpolynomial_sum.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.isl_pw_qpolynomial_sum.restype = ctypes.c_void_p

def barvinok_sum_polyhedron(set_, pw_aff):
    """
    Return an isl.PwQPolynomial representing ∑_{x∈set_} pw_aff(x).
    """
    set_ptr = set_._ptr
    aff_ptr = pw_aff._ptr

    res_ptr = lib.isl_pw_qpolynomial_sum(set_ptr, aff_ptr)
    return isl.PwQPolynomial._from_ptr(res_ptr)