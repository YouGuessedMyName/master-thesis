import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, N
import islpy as isl


def plot_exponential_with_pw_aff(
    a, b, c, d,
    x_points,
    y_points,
    pw_aff=None,
    *,
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

    x = symbols("x")
    expr = c * a**(x-d) + b

    if xlim is None:
        xmin = min(x_points) - padding
        xmax = max(x_points) + padding
    else:
        xmin, xmax = xlim

    xs = np.linspace(float(xmin), float(xmax), num_points)

    # Exponential evaluation (keeps symbolic precision until here)
    ys_exp = np.array([
        float(N(expr.subs(x, value)))
        for value in xs
    ])

    created_axes = ax is None
    if created_axes:
        fig, ax = plt.subplots()

    # Exponential curve
    ax.plot(
        xs,
        ys_exp,
        label=r"$y=c a^{(x-d)}+b$"
    )

    # Original points
    ax.scatter(
        [float(v) for v in x_points],
        [float(v) for v in y_points],
        color="red",
        zorder=5,
        label="Data points",
    )

    # islpy PwAff curve
    if pw_aff is not None:
        pw_xs = []
        pw_ys = []

        for value in xs:
            try:
                point = isl.Val.read_from_str(
                    pw_aff.get_ctx(),
                    str(value)
                )

                result = pw_aff.eval(point)

                pw_xs.append(value)
                pw_ys.append(float(result.to_python()))

            except Exception:
                # outside domain of the PwAff
                pass

        ax.plot(
            pw_xs,
            pw_ys,
            label="islpy PwAff"
        )

    ax.set_xlim(xmin, xmax)

    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.legend()

    return ax.figure if created_axes else ax