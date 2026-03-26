#include <isl/set.h>
#include <isl/polynomial.h>
#include <barvinok/barvinok.h>

char* barvinok_sum_str(const char* set_str, const char* aff_str) {
    isl_ctx *ctx = isl_ctx_alloc();

    isl_set *set = isl_set_read_from_str(ctx, set_str);
    isl_pw_aff *aff = isl_pw_aff_read_from_str(ctx, aff_str);

    isl_pw_qpolynomial *qp =
        isl_pw_qpolynomial_from_pw_aff(aff);

    isl_pw_qpolynomial *res =
        barvinok_summate(set, qp);   // <-- THIS is the key change

    char *res_str = isl_pw_qpolynomial_to_str(res);

    isl_pw_qpolynomial_free(res);
    isl_ctx_free(ctx);

    return res_str;
}