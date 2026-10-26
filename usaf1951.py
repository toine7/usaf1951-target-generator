#!/usr/bin/env python3
"""Generate an SVG of the 1951 USAF resolving power test target (MIL-STD-150A).

Element geometry follows MIL-STD-150A, 5.1.1.7 / Figure 7:
    resolution  R = 2 ** (group + (element - 1) / 6)   [line pairs per mm]
    line width  w = 1 / (2 R)                           [mm]
    each element = two patterns of three lines at right angles,
    lines 5w long and w wide, separated by spaces w wide,
    the two patterns separated by 2w (= 1/R).

The standard does not dimension the overall arrangement, so the spiral layout
(columns, reference square, label positions) reproduces the original 1951
Buckbee-Mears chart. Each "layer" holds an even group G and the odd group G+1:

    normal layer                      mirrored layer (G = 0, 4, 8, ...)
      G            G+1                  G+1            G
    2 =|||  +----+ |||= 1             1 =|||  +----+ |||= 2
    3 =|||  |    | |||= 2             2 =|||  |    | |||= 3
    4 =|||  +----+ |||= 3             3 =|||  +----+ |||= 4
    5 =|||  [next] |||= 4             4 =|||  [next] |||= 5
    6 =|||  layer  |||= 5             5 =|||  layer  |||= 6
                   |||= 6             6 =|||
                   G                   G
                |||  =  1           1  =  |||

Element 1 of group G sits at the bottom, elements 2-6 of G form the outer
column, elements 1-6 of G+1 the inner column. The next layer (G+2, G+3) is a
quarter-scale copy, mirrored, nested below the reference square.

The SVG is drawn at true physical size in millimetres (use --scale to enlarge).
"""

import argparse
import math

R6 = 2 ** (-1 / 6)  # size ratio between successive elements

# Layout constants, in units of the line width of element 1 of the layer's even group.
ELEMENT_GAP = 2.0  # space below an element, in its own line widths
SQUARE_W = 6.45
SQUARE_H = 7.42
SQUARE_GAP_LEFT = 2 * R6  # 2 line widths of element 2
SQUARE_GAP_RIGHT = 1.0  # 2 line widths of odd-group element 1
CHILD_GAP_X = 0.45  # next layer, right of the even-group column
CHILD_Y = 9.15  # next layer top, measured from layer top

EVEN_COL_W = 12 * R6  # width of element 2
ODD_COL_W = 6.0  # width of odd-group element 1
LAYER_W = EVEN_COL_W + SQUARE_GAP_LEFT + SQUARE_W + SQUARE_GAP_RIGHT + ODD_COL_W
LAYER_H = sum(5 * R6**k + ELEMENT_GAP * R6**k for k in range(1, 5)) + 5 * R6**5

# Label digit heights and offsets (same units).
GROUP_LABEL_H = 3.0
GROUP_LABEL_GAP = 0.8
EVEN_LABEL_H = 2.3
EVEN_LABEL_GAP = 1.7
ODD_LABEL_H = 1.3
ODD_LABEL_GAP = 0.9
DIGIT_HEIGHT_EM = 0.716  # digit height of Arial/Helvetica as a fraction of font-size
FONT_FAMILY = "Arial, Helvetica, sans-serif"


def lp_per_mm(group, element):
    return 2 ** (group + (element - 1) / 6)


def line_width(group, element):
    """Line width in mm."""
    return 1 / (2 * lp_per_mm(group, element))


def group_text(group):
    return str(group).replace("-", "−")


class Layer:
    """Maps a layer's local coordinates (line-width units, unmirrored) to mm."""

    def __init__(self, svg, group, x0, y0, mirrored):
        self.svg = svg
        self.group = group
        self.x0 = x0
        self.y0 = y0
        self.u = line_width(group, 1)
        self.mirrored = mirrored

    def x(self, x, width=0.0):
        """Absolute left edge (mm) of a box at local x with the given width."""
        if self.mirrored:
            x = LAYER_W - x - width
        return self.x0 + x * self.u

    def y(self, y):
        return self.y0 + y * self.u

    def rect(self, x, y, width, height):
        self.svg.rect(self.x(x, width), self.y(y), width * self.u, height * self.u)

    def text(self, label, x, baseline, height, anchor):
        if self.mirrored:
            anchor = {"start": "end", "end": "start"}.get(anchor, anchor)
        self.svg.text(label, self.x(x), self.y(baseline), height * self.u, anchor)

    def element(self, x, y, s, vertical_first):
        """Draw an element of line width s (local units) with top-left corner at (x, y)."""
        bars_v = x if vertical_first else x + 7 * s
        bars_h = x + 7 * s if vertical_first else x
        for i in range(3):
            self.rect(bars_v + 2 * i * s, y, s, 5 * s)
            self.rect(bars_h, y + 2 * i * s, 5 * s, s)

    def draw(self):
        g = self.group

        # Even group, elements 2-6: outer column, left-aligned, labels outside.
        self.text(group_text(g), EVEN_COL_W / 2, -GROUP_LABEL_GAP, GROUP_LABEL_H, "middle")
        y = 0.0
        for e in range(2, 7):
            s = R6 ** (e - 1)
            self.element(0, y, s, vertical_first=False)
            self.text(str(e), -EVEN_LABEL_GAP, y + 2.5 * s + EVEN_LABEL_H / 2, EVEN_LABEL_H, "end")
            y += 5 * s + ELEMENT_GAP * s

        # Reference square.
        self.rect(EVEN_COL_W + SQUARE_GAP_LEFT, 0, SQUARE_W, SQUARE_H)

        # Odd group, elements 1-6: inner column, right-aligned, labels outside.
        self.text(group_text(g + 1), LAYER_W - ODD_COL_W / 2, -GROUP_LABEL_GAP, GROUP_LABEL_H, "middle")
        y = 0.0
        for e in range(1, 7):
            s = R6 ** (e - 1) / 2
            self.element(LAYER_W - 12 * s, y, s, vertical_first=True)
            self.text(str(e), LAYER_W + ODD_LABEL_GAP, y + 2.5 * s + ODD_LABEL_H / 2, ODD_LABEL_H, "start")
            y += 5 * s + ELEMENT_GAP * s

        # Even group, element 1: bottom corner, group number repeated above its label.
        y = LAYER_H - 5
        self.element(LAYER_W - 12, y, 1, vertical_first=True)
        self.text(group_text(g), LAYER_W + ODD_LABEL_GAP, y, GROUP_LABEL_H, "start")
        self.text("1", LAYER_W + ODD_LABEL_GAP, y + 2.5 + EVEN_LABEL_H / 2, EVEN_LABEL_H, "start")

    def child(self):
        """Next layer (groups + 2), quarter scale, nested below the square."""
        x = self.x(EVEN_COL_W + CHILD_GAP_X, LAYER_W / 4)
        return Layer(self.svg, self.group + 2, x, self.y(CHILD_Y), not self.mirrored)


class Svg:
    def __init__(self):
        self.rects = []
        self.texts = []

    def rect(self, x, y, w, h):
        self.rects.append((x, y, w, h))

    def text(self, label, x, baseline, digit_height, anchor):
        self.texts.append((label, x, baseline, digit_height / DIGIT_HEIGHT_EM, anchor))

    def render(self, x0, y0, width, height, scale, fg, bg):
        f = lambda v: f"{v:.6f}".rstrip("0").rstrip(".")
        out = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(width * scale)}mm" height="{f(height * scale)}mm" '
            f'viewBox="{f(x0)} {f(y0)} {f(width)} {f(height)}">',
            f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(width)}" height="{f(height)}" fill="{bg}"/>',
            f'<g fill="{fg}">',
        ]
        out += [f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>' for x, y, w, h in self.rects]
        out.append("</g>")
        out.append(f'<g fill="{fg}" font-family="{FONT_FAMILY}">')
        out += [
            f'<text x="{f(x)}" y="{f(y)}" font-size="{f(size)}" text-anchor="{anchor}">{label}</text>'
            for label, x, y, size, anchor in self.texts
        ]
        out.append("</g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


def build(first_group, last_group, scale, negative):
    svg = Svg()
    # Groups -2, 2, 6, ... are drawn in the normal orientation, 0, 4, 8, ... mirrored.
    outer_mirrored = ((first_group + 2) // 2) % 2 == 1
    layer = Layer(svg, first_group, 0.0, 0.0, outer_mirrored)
    outer_u = layer.u
    while True:
        layer.draw()
        if layer.group + 1 >= last_group:
            break
        layer = layer.child()

    # Margins: the odd-group side also carries the bottom group number (e.g. "−2").
    even_side, odd_side = 4.5 * outer_u, 7 * outer_u
    left, right = (odd_side, even_side) if outer_mirrored else (even_side, odd_side)
    top, bottom = 4.5 * outer_u, 2 * outer_u
    fg, bg = ("white", "black") if negative else ("black", "white")
    width = left + LAYER_W * outer_u + right
    height = top + LAYER_H * outer_u + bottom
    return svg.render(-left, -top, width, height, scale, fg, bg)


def print_table(first_group, last_group):
    print("group element    lp/mm   line width (um)")
    for g in range(first_group, last_group + 1):
        for e in range(1, 7):
            print(f"{g:5d} {e:7d} {lp_per_mm(g, e):8.2f} {line_width(g, e) * 1000:12.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--first-group", type=int, default=2, help="outermost group, must be even (default 2)")
    p.add_argument("--last-group", type=int, default=7, help="innermost group, must be odd (default 7)")
    p.add_argument("--scale", type=float, default=1.0, help="magnification of the printed size (default 1 = true size)")
    p.add_argument("--negative", action="store_true", help="white pattern on black background")
    p.add_argument("--table", action="store_true", help="also print the resolution table")
    p.add_argument("-o", "--output", default=None, help="output file (default usaf1951_groups<first>-<last>.svg)")
    args = p.parse_args()

    if args.first_group % 2 or not args.last_group % 2 or args.last_group <= args.first_group:
        p.error("groups come in pairs: --first-group must be even, --last-group odd and larger")

    output = args.output or f"usaf1951_groups{args.first_group}-{args.last_group}.svg"
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(build(args.first_group, args.last_group, args.scale, args.negative))
    print(f"wrote {output}")
    if args.table:
        print_table(args.first_group, args.last_group)


if __name__ == "__main__":
    main()
