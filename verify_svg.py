#!/usr/bin/env python3
"""Check every bar of a generated USAF 1951 SVG against MIL-STD-150A Figure 7.

    python verify_svg.py usaf1951_groups2-7.svg 2 7

For each group/element it finds the six bars of width w = 1/(2R) mm and length 5w,
and checks the three-line spacing (pitch 2w), the alignment of the two patterns and
the 2w gap between them. It also checks that no two shapes overlap.
"""

import re
import sys

TOL = 2e-6  # mm; the generator writes coordinates with 1 nm precision


def close(a, b):
    return abs(a - b) <= TOL


def overlap(a, b):
    return (a[0] < b[0] + b[2] - TOL and b[0] < a[0] + a[2] - TOL
            and a[1] < b[1] + b[3] - TOL and b[1] < a[1] + a[3] - TOL)


def check_element(rects, group, element):
    """Return (indices of the element's bars, list of errors)."""
    lp = 2 ** (group + (element - 1) / 6)
    w = 1 / (2 * lp)
    bars = [i for i, r in enumerate(rects)
            if close(min(r[2], r[3]), w) and close(max(r[2], r[3]), 5 * w)]
    vert = sorted((rects[i] for i in bars if rects[i][3] > rects[i][2]), key=lambda r: r[0])
    horz = sorted((rects[i] for i in bars if rects[i][2] > rects[i][3]), key=lambda r: r[1])
    tag = f"group {group} element {element} ({lp:.2f} lp/mm, w = {w * 1000:.3f} um)"
    if len(vert) != 3 or len(horz) != 3:
        return bars, [f"{tag}: found {len(vert)} vertical and {len(horz)} horizontal bars"]

    errors = []
    if not all(close(vert[k + 1][0] - vert[k][0], 2 * w) and close(vert[k][1], vert[0][1]) for k in range(2)):
        errors.append(f"{tag}: vertical lines not spaced by w")
    if not all(close(horz[k + 1][1] - horz[k][1], 2 * w) and close(horz[k][0], horz[0][0]) for k in range(2)):
        errors.append(f"{tag}: horizontal lines not spaced by w")
    if not close(vert[0][1], horz[0][1]):
        errors.append(f"{tag}: patterns not aligned")
    v_left, v_right = vert[0][0], vert[2][0] + w
    h_left, h_right = horz[0][0], horz[0][0] + 5 * w
    gap = h_left - v_right if h_left > v_left else v_left - h_right
    if not close(gap, 2 * w):
        errors.append(f"{tag}: gap between patterns is {gap / w:.4f} w, expected 2 w")
    if not errors:
        print(f"ok  {tag}")
    return bars, errors


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    path, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    src = open(path, encoding="utf-8").read()
    # Pattern shapes only: the background rect carries a fill attribute and does not match.
    rects = [tuple(float(v) for v in m) for m in re.findall(
        r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/>', src)]

    errors, used = [], set()
    for group in range(first, last + 1):
        for element in range(1, 7):
            bars, errs = check_element(rects, group, element)
            used.update(bars)
            errors += errs

    others = [r for i, r in enumerate(rects) if i not in used]
    print(f"\n{len(used)} bars checked, {len(others)} reference squares")
    n_overlap = sum(overlap(rects[i], rects[j]) for i in range(len(rects)) for j in range(i + 1, len(rects)))
    if n_overlap:
        errors.append(f"{n_overlap} overlapping shapes")

    if errors:
        print("\nERRORS:\n" + "\n".join(errors))
        sys.exit(1)
    print("all elements conform to MIL-STD-150A")


if __name__ == "__main__":
    main()
