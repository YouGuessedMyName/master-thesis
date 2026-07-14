import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, N
import islpy as isl

from sym_adjpdr.frames import Frame, State


def plot_exponential_with_pw_aff(
    a, b, c, d,
    x_points,
    y_points,
    F: Frame = None,
    state : isl.Point = None,
    variable_index: int = None,
    xlim=None,
    ylim=None,
    num_points=500,
    padding=0.5,
    ax=None,
):
    """
    Plot y = c*a^x + b together with fitted points and an optional islpy PwAff.

    Parameters
    ----------
    a, b, c : sympy expressions
        Parameters of exponential.
    x_points, y_points : sequences
        Points used for fitting.
    pw_aff : islpy.PwAff, optional
        Piecewise affine function to plot alongside.
    """

    x = symbols("x", integer=True)
    expr = c * a**(x-d) + b

    if xlim is None:
        xmin = min(x_points) - padding
        xmax = max(x_points) + padding
    else:
        xmin, xmax = xlim

    xs = np.arange(int(np.ceil(xmin)), int(np.floor(xmax)) + 1, step=1)

    # Exponential evaluation (keeps symbolic precision until here)
    ls = []
    for value in xs:
        try:
            conv = N(expr.subs(x, value))
            ls.append(float(conv))
        except:
            pass
    ys_exp = np.array(ls)

    created_axes = ax is None
    if created_axes:
        fig, ax = plt.subplots()

    # Original points
    ax.scatter(
        [float(v) for v in x_points],
        [float(v) for v in y_points],
        color="red",
        zorder=5,
        label="p0,p1,p2",
    )

    # Exponential curve
    ax.plot(
        xs,
        ys_exp,
        label="e"
    )

    

    # islpy PwAff curve
    if F is not None:
        pw_xs = []
        pw_ys = []

        for value in xs:
            # try:
            val = isl.Val.read_from_str(
                F.pw.get_ctx(),
                str(round(value))
            )
            point = state.copy().set_coordinate_val(isl.dim_type.set, variable_index, val)
            try:
                result = F.eval(point)

                pw_xs.append(round(value))
                pw_ys.append(float(result))

            except Exception:
                # outside domain of the PwAff
                pass

        ax.plot(
            pw_xs,
            pw_ys,
            label="a"
        )

    ax.set_xlim(xmin, xmax)

    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.legend()

    return ax.figure if created_axes else ax