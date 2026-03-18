ZERO_COLOR = "#FFFFFF"
ONE_COLOR = "#FF0000"
def blend_colors(c1: str, c2: str, factor: float) -> str:
    """Blend two colors in HEX format. #RRGGBB.
    Args:
        color1 (str): Color 1 in HEX format #RRGGBB
        color2 (str): Color 2 in HEX format #RRGGBB
        factor (float): The fraction of the resulting color that should come from color1."""
    r1 = int("0x" + c1[1:3], 0)
    g1 = int("0x" + c1[3:5], 0)
    b1 = int("0x" + c1[5:7], 0)
    r2 = int("0x" + c2[1:3], 0)
    g2 = int("0x" + c2[3:5], 0)
    b2 = int("0x" + c2[5:7], 0)
    r_res = int(factor * r1 + (1 - factor) * r2)
    g_res = int(factor * g1 + (1 - factor) * g2)
    b_res = int(factor * b1 + (1 - factor) * b2)
    return "#" + "".join("%02x" % i for i in [r_res, g_res, b_res])


def vis_frame(F, vis, zero_color: str = ZERO_COLOR, one_color: str = ONE_COLOR):
    for i,fi in enumerate(F):
        color = blend_colors(one_color, zero_color, fi)
        print(i,fi, color)
        vis.highlight_state(i, color=color)