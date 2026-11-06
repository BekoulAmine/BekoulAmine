"""Generates assets/banner.svg: a pixel-art Teyvat night scene (W x H logical pixels, scaled by the viewer).

Usage: python banner.py [out_path]
"""
import math, os, random, sys
import xml.etree.ElementTree as ET

W, H = 200, 60

GLYPHS = {  # 5x5 pixel font, rows separated by "/"
    "A": ".###./#...#/#####/#...#/#...#", "B": "####./#...#/####./#...#/####.",
    "C": ".####/#..../#..../#..../.####", "D": "####./#...#/#...#/#...#/####.",
    "E": "#####/#..../####./#..../#####", "F": "#####/#..../####./#..../#....",
    "G": ".####/#..../#..##/#...#/.####", "H": "#...#/#...#/#####/#...#/#...#",
    "I": "#####/..#../..#../..#../#####", "L": "#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#...#/#...#", "N": "#...#/##..#/#.#.#/#..##/#...#",
    "O": ".###./#...#/#...#/#...#/.###.", "R": "####./#...#/####./#..#./#...#",
    "S": ".####/#..../.###./....#/####.", "T": "#####/..#../..#../..#../..#..",
    "V": "#...#/#...#/#...#/.#.#./..#..", "W": "#...#/#...#/#.#.#/##.##/#...#",
    "Y": "#...#/.#.#./..#../..#../..#..", " ": "...../...../...../...../.....",
}

PAIMON = [
    "....g.g....", "....ggg....", "...wwwww...", "..wwwwwww..", "..wsssssw..", "..wsesesw..",
    "..wsssssw..", "...wwsww...", "..bbwwwbb..", ".bbbwwwbbb.", ".bdbwwwbdb.", "..d.www.d..", ".....w.w...",
]
PAIMON_PAL = {"g": "#d3bc8e", "w": "#f4f4f4", "s": "#f6d7b8", "e": "#3a7bd5", "b": "#5f8fe0", "d": "#243a73"}

GEM = ["..b..", ".bwb.", "bwbbb", ".bbb.", "..b.."]
GEM_PAL = {"b": "#8fb4ff", "w": "#ffffff"}

TOWER = ["..rrr..", ".rrrrr.", "..sss..", "..sds..", "..sss..", ".sssss.", ".sssss.", "sssdsss"]
TOWER_PAL = {"r": "#b5523b", "s": "#8a8fa8", "d": "#3b3f58"}

BANDS = [(0, "#0d0e1a"), (8, "#14162a"), (14, "#1b1d2a"), (19, "#262a48"), (24, "#3d4a6b"),
         (29, "#6b6a8a"), (34, "#a58f7c"), (39, "#d3bc8e")]

TITLE, SUBTITLE = "WELCOME TO MY TEYVAT", "A TRAVELER FROM ALGIERS"


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{extra}/>'


def sprite(rows, pal, ox, oy):
    """Rects for a character grid, merging horizontal runs of one colour."""
    assert len({len(r) for r in rows}) == 1, "ragged sprite"
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            run = x
            while run < len(row) and row[run] == ch:
                run += 1
            out.append(rect(ox + x, oy + y, run - x, 1, pal[ch]))
            x = run
    return out


def text(s, x, y, color):
    out = []
    for i, ch in enumerate(s):
        rows = GLYPHS[ch].split("/")
        out += sprite(rows, {"#": color}, x + i * 6, y)
    return out


def hill(x):
    return int(50 + 2 * math.sin(x / 13) + 1.5 * math.sin(x / 5.1))


def ridge(peaks, slope):
    """Skyline of overlapping mountains: each peak (x, y) slopes down on both sides."""
    return lambda x: int(min(py + abs(x - px) * slope for px, py in peaks))


FAR = ridge([(25, 33), (70, 29), (115, 34), (160, 30), (205, 33)], 0.55)
NEAR = ridge([(48, 40), (100, 38), (150, 41), (198, 39)], 0.7)


def stair(top, dy, fill):
    """One filled path under a pixel-stepped skyline: column x spans [x, x+1] and starts at top(x)+dy."""
    d = f"M0 {H}V{top(0) + dy}" + "".join(f"H{x}V{top(x) + dy}" for x in range(1, W)) + f"H{W}V{H}Z"
    return f'<path d="{d}" fill="{fill}"/>'


def build() -> str:
    rng = random.Random(7)
    tw = (len(TITLE) * 6 - 1, len(SUBTITLE) * 6 - 1)
    tx, sx = (W - tw[0]) // 2, (W - tw[1]) // 2
    keep_out = [(tx - 2, 7, tx + tw[0] + 2, 16), (sx - 2, 17, sx + tw[1] + 2, 26)]

    defs = ["<style>.fa{animation:a 1.2s step-end infinite}.fb{animation:b 1.2s step-end infinite}"
            ".bob{animation:bob 2s step-end infinite}.t{animation:t 2.4s step-end infinite}"
            "@keyframes a{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes b{0%,49%{opacity:0}50%,100%{opacity:1}}"
            "@keyframes bob{0%,49%{transform:translateY(0)}50%,100%{transform:translateY(1px)}}"
            "@keyframes t{0%,59%{opacity:1}60%,100%{opacity:.2}}</style>"]
    body = []
    for i, (y, color) in enumerate(BANDS):
        end = BANDS[i + 1][0] if i + 1 < len(BANDS) else H
        body.append(rect(0, y, W, end - y, color))
        if i:  # checker dither strip on the boundary with the previous band
            prev = BANDS[i - 1][1]
            defs.append(f'<pattern id="d{i}" width="2" height="2" patternUnits="userSpaceOnUse">'
                        f'{rect(0, 0, 2, 2, prev)}{rect(0, 0, 1, 1, color)}{rect(1, 1, 1, 1, color)}</pattern>')
            body.append(f'<rect x="0" y="{y - 2}" width="{W}" height="2" fill="url(#d{i})"/>')

    for _ in range(90):  # stars
        x, y = rng.randrange(W), rng.randrange(27)
        if any(a <= x <= c and b <= y <= d for a, b, c, d in keep_out):
            continue
        color = rng.choice(["#ece5d8", "#d3bc8e", "#8fb4ff"])
        cls = f' class="t" style="animation-delay:-{rng.random() * 2.4:.1f}s"' if rng.random() < 0.4 else ""
        body.append(rect(x, y, 1, 1, color, cls))

    mx, my, mr = 178, 11, 7  # moon with craters
    for y in range(my - mr, my + mr + 1):
        for x in range(mx - mr, mx + mr + 1):
            if (x - mx) ** 2 + (y - my) ** 2 <= mr * mr:
                body.append(rect(x, y, 1, 1, "#ece5d8"))
    for cx, cy in [(175, 9), (180, 13), (177, 14)]:
        body.append(rect(cx, cy, 1, 1, "#d3bc8e"))

    # hazy far range, dark near range, then Anemo-green hills
    body += [stair(FAR, 0, "#6b6a8a"), stair(NEAR, 0, "#2b3350")]
    body += [stair(hill, 0, "#4fa38a"), stair(hill, 1, "#2e6b5e"), stair(hill, 3, "#1f3d3a")]

    wx = 14  # windmill: tower plus two blade frames that alternate
    y0 = hill(wx) - 6
    body += sprite(TOWER, TOWER_PAL, wx - 3, y0)
    cx, cy = wx, y0 + 1
    plus = [(cx + k * dx, cy + k * dy) for k in range(1, 6) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    diag = [(cx + k * dx, cy + k * dy) for k in range(1, 5) for dx in (1, -1) for dy in (1, -1)]
    for cls, pts in (("fa", plus), ("fb", diag)):
        body.append(f'<g class="{cls}">' + "".join(rect(x, y, 1, 1, "#ece5d8") for x, y in pts) + "</g>")
    body.append(rect(cx, cy, 1, 1, "#3b3f58"))

    body.append('<g class="bob">' + "".join(sprite(PAIMON, PAIMON_PAL, 176, 24)) + "</g>")
    for gx, gy, d in [(tx - 11, 8, 0), (tx + tw[0] + 6, 8, 1.2)]:
        body.append(f'<g class="t" style="animation-delay:-{d}s">' + "".join(sprite(GEM, GEM_PAL, gx, gy)) + "</g>")

    body += text(TITLE, tx + 1, 9, "#0d0e1a") + text(TITLE, tx, 8, "#d3bc8e")
    body += text(SUBTITLE, sx + 1, 19, "#0d0e1a") + text(SUBTITLE, sx, 18, "#74c2a8")

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" shape-rendering="crispEdges" role="img" '
            f'aria-label="Welcome to my Teyvat: a traveler from Algiers"><defs>{"".join(defs)}</defs>{"".join(body)}</svg>')


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/banner.svg"
    svg = build()
    ET.fromstring(svg)  # must be well-formed XML
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"wrote {out} ({len(svg) // 1024} KB)")
