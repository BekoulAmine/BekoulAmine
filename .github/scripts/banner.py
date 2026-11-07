"""Generates the pixel-art assets in assets/: banner, footer, section headings, divider and the tech-stack panel.

Everything is drawn from one 5x5 pixel font, so the README has no external image dependencies.
Usage: python banner.py [out_dir]
"""
import math, os, random, sys
import xml.etree.ElementTree as ET

W, H = 200, 60
GREEN, WHITE, DIM, GRAY, PANEL, INK = "#79ff97", "#e6edf3", "#8b949e", "#30363d", "#161b22", "#0d1117"

GLYPHS = {  # 5x5 pixel font, rows separated by "/"
    "A": ".###./#...#/#####/#...#/#...#", "B": "####./#...#/####./#...#/####.",
    "C": ".####/#..../#..../#..../.####", "D": "####./#...#/#...#/#...#/####.",
    "E": "#####/#..../####./#..../#####", "F": "#####/#..../####./#..../#....",
    "G": ".####/#..../#..##/#...#/.####", "H": "#...#/#...#/#####/#...#/#...#",
    "I": "#####/..#../..#../..#../#####", "J": "..###/...#./...#./#..#./.##..",
    "K": "#...#/#..#./###../#..#./#...#", "L": "#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#...#/#...#", "N": "#...#/##..#/#.#.#/#..##/#...#",
    "O": ".###./#...#/#...#/#...#/.###.", "P": "####./#...#/####./#..../#....",
    "Q": ".###./#...#/#.#.#/#..#./.##.#", "R": "####./#...#/####./#..#./#...#",
    "S": ".####/#..../.###./....#/####.", "T": "#####/..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/.###.", "V": "#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#.#.#/##.##/#...#", "X": "#...#/.#.#./..#../.#.#./#...#",
    "Y": "#...#/.#.#./..#../..#../..#..", " ": "...../...../...../...../.....",
}

ROCKET = [
    "...w...", "..www..", "..wbw..", "..www..", ".wwwww.", ".wwwww.", ".rwwwr.", ".r.w.r.", "...o...", "..oyo..", "...y...",
]
ROCKET_PAL = {"w": WHITE, "b": "#58a6ff", "r": "#f85149", "o": "#ffa657", "y": "#f2cc60"}

GEM = ["..b..", ".bwb.", "bwbbb", ".bbb.", "..b.."]
GEM_PAL = {"b": GREEN, "w": WHITE}

TOWER = ["..rrr..", ".rrrrr.", "..sss..", "..sds..", "..sss..", ".sssss.", ".sssss.", "sssdsss"]
TOWER_PAL = {"r": "#b5523b", "s": "#8a8fa8", "d": "#3b3f58"}

# deep blue night fading through teal into a neon-green horizon
BANDS = [(0, "#0d1117"), (8, "#111a26"), (14, "#152238"), (19, "#1a2f4d"), (24, "#233f66"),
         (29, "#2a6a7a"), (34, "#3a9c6a"), (39, "#79ff97")]

TITLE, SUBTITLE, MOTTO = "AMINE BEKOUL", "FULL STACK DEVELOPER", "BUILD BREAK LEARN REPEAT"
HEADINGS = {"stats": "STATS", "stack": "TECH STACK", "snake": "SNAKE GAME", "learning": "LEARNING", "connect": "CONNECT"}
STACK = [
    ("LANGUAGES", GREEN, ["PYTHON", "JAVASCRIPT", "C", "JAVA"]),
    ("FRONTEND", "#58a6ff", ["REACT", "VITE", "TAILWIND", "HTML", "CSS"]),
    ("BACKEND", "#ffa657", ["DJANGO", "DRF", "POSTGRESQL"]),
    ("TOOLS", "#d2a8ff", ["GIT", "GITHUB", "LINUX", "POSTMAN", "VS CODE"]),
]


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
        out += sprite(GLYPHS[ch].split("/"), {"#": color}, x + i * 6, y)
    return out


def text_width(s):
    return len(s) * 6 - 1


def svg(w, h, body, label, scale=None, defs="", y0=0):
    size = f' width="{w * scale}" height="{h * scale}"' if scale else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {y0} {w} {h}"{size} shape-rendering="crispEdges" '
            f'role="img" aria-label="{label}">{f"<defs>{defs}</defs>" if defs else ""}{"".join(body)}</svg>')


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


def scene(footer=False) -> str:
    """Header: full scene. Footer: same scene cropped to the lower sky, motto only, no moon or rocket."""
    rng = random.Random(7)
    lines = [(MOTTO, 20, GREEN)] if footer else [(TITLE, 8, GREEN), (SUBTITLE, 18, WHITE)]
    xs = [(W - text_width(s)) // 2 for s, _, _ in lines]
    keep_out = [(x - 2, y - 1, x + len(s) * 6 + 1, y + 8) for x, (s, y, _) in zip(xs, lines)]

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
        color = rng.choice([WHITE, GREEN, "#58a6ff"])
        cls = f' class="t" style="animation-delay:-{rng.random() * 2.4:.1f}s"' if rng.random() < 0.4 else ""
        body.append(rect(x, y, 1, 1, color, cls))

    if not footer:  # moon with craters
        mx, my, mr = 178, 11, 7
        body += [rect(x, y, 1, 1, WHITE) for y in range(my - mr, my + mr + 1) for x in range(mx - mr, mx + mr + 1)
                 if (x - mx) ** 2 + (y - my) ** 2 <= mr * mr]
        body += [rect(cx, cy, 1, 1, "#c9d1d9") for cx, cy in [(175, 9), (180, 13), (177, 14)]]

    # dark teal far range, darker near range, then green hills
    body += [stair(FAR, 0, "#0f3b4a"), stair(NEAR, 0, "#091f2b")]
    body += [stair(hill, 0, "#5fd67b"), stair(hill, 1, "#2f8f55"), stair(hill, 3, "#143d2a")]

    wx = 14  # windmill: tower plus two blade frames that alternate
    y0 = hill(wx) - 6
    body += sprite(TOWER, TOWER_PAL, wx - 3, y0)
    cx, cy = wx, y0 + 1
    plus = [(cx + k * dx, cy + k * dy) for k in range(1, 6) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    diag = [(cx + k * dx, cy + k * dy) for k in range(1, 5) for dx in (1, -1) for dy in (1, -1)]
    for cls, pts in (("fa", plus), ("fb", diag)):
        body.append(f'<g class="{cls}">' + "".join(rect(x, y, 1, 1, WHITE) for x, y in pts) + "</g>")
    body.append(rect(cx, cy, 1, 1, "#3b3f58"))

    if not footer:
        body.append('<g class="bob">' + "".join(sprite(ROCKET, ROCKET_PAL, 178, 22)) + "</g>")
    s0, y0_, _ = lines[0]
    for gx, d in [(xs[0] - 11, 0), (xs[0] + len(s0) * 6 + 5, 1.2)]:
        body.append(f'<g class="t" style="animation-delay:-{d}s">' + "".join(sprite(GEM, GEM_PAL, gx, y0_)) + "</g>")

    for (s, y, color), x in zip(lines, xs):
        body += text(s, x + 1, y + 1, INK) + text(s, x, y, color)

    label = ", ".join(s.title() for s, _, _ in lines)
    return svg(W, H - 14 if footer else H, body, label, defs="".join(defs), y0=14 if footer else 0)


def heading(s) -> str:
    w = 8 + text_width(s)
    body = sprite(GEM, GEM_PAL, 0, 0) + text(s, 8, 0, GREEN) + [rect(0, 7, w, 1, GRAY), rect(0, 7, 5, 1, GREEN)]
    return svg(w, 8, body, s.title(), scale=3)


def divider() -> str:
    w, gem_x = 200, 97
    body = [rect(x, 2, 1, 1, GRAY) for x in range(0, w, 2) if not gem_x - 3 <= x <= gem_x + 7]
    return svg(w, 5, body + sprite(GEM, GEM_PAL, gem_x, 0), "divider")


def stack() -> str:
    label_w, chip_h, pitch, body, width = 60, 13, 17, [], 0
    for r, (name, color, items) in enumerate(STACK):
        y, x = r * pitch, label_w
        body += text(name, 0, y + 4, DIM)
        for item in items:
            cw = text_width(item) + 8
            body += [rect(x, y, cw, chip_h, color), rect(x + 1, y + 1, cw - 2, chip_h - 2, PANEL)]
            body += text(item, x + 4, y + 4, WHITE)
            x += cw + 3
        width = max(width, x - 3)
    return svg(width, (len(STACK) - 1) * pitch + chip_h, body, "Tech stack", scale=3)


def outputs() -> dict:
    files = {"banner.svg": scene(), "footer.svg": scene(footer=True), "divider.svg": divider(), "stack.svg": stack()}
    files.update({f"h-{key}.svg": heading(s) for key, s in HEADINGS.items()})
    return files


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "assets"
    os.makedirs(out_dir, exist_ok=True)
    for name, content in outputs().items():
        ET.fromstring(content)  # must be well-formed XML
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"wrote {name} ({len(content) // 1024 or '<1'} KB)")
