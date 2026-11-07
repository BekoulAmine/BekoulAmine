"""Builds pixel-styled stat cards (stats, languages, activity) as SVGs from the GitHub GraphQL API.

Self-hosted because the public github-readme-stats / trophy / activity-graph instances get paused.
Usage: GITHUB_TOKEN=... python cards.py <username> <out_dir>
"""
import datetime, json, os, sys, urllib.request
from html import escape

import banner  # pixel font for the card titles

BG, GREEN, TEXT, DIM, LINE = "#0d1117", "#79ff97", "#e6edf3", "#8b949e", "#30363d"
FONT = "font-family=\"'Segoe UI', Ubuntu, sans-serif\""
QUERY = """query($login: String!) { user(login: $login) {
  followers { totalCount }
  repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
    totalCount
    nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
  }
  contributionsCollection {
    totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
  }
} }"""


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    body = json.load(urllib.request.urlopen(req, timeout=30))
    if body.get("errors") or not body.get("data", {}).get("user"):
        sys.exit(f"GraphQL error: {body.get('errors')}")
    return body["data"]["user"]


def streaks(days: list) -> tuple:
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today not done yet doesn't break the streak
        i -= 1
    current = 0
    while i >= 0 and counts[i]:
        current, i = current + 1, i - 1
    return current, longest


def card(w: int, h: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" fill="{BG}" stroke="{LINE}"/>'
        f'<g transform="translate(25 20) scale(3)" shape-rendering="crispEdges">{"".join(banner.text(title, 0, 0, GREEN))}</g>'
        f'{body}</svg>'
    )


def stats_svg(u: dict) -> str:
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    cur, best = streaks(days)
    rows = [
        ("⭐", "Stars earned", sum(r["stargazerCount"] for r in u["repositories"]["nodes"])),
        ("📜", "Commits (this year)", cc["totalCommitContributions"]),
        ("🔀", "Pull requests", cc["totalPullRequestContributions"]),
        ("❗", "Issues", cc["totalIssueContributions"]),
        ("👀", "Reviews", cc["totalPullRequestReviewContributions"]),
        ("📦", "Public repos", u["repositories"]["totalCount"]),
        ("🔥", "Current streak", f"{cur} days"),
        ("🏆", "Longest streak", f"{best} days"),
    ]
    body = ""
    for i, (icon, label, val) in enumerate(rows):
        x, y = 25 + (i // 4) * 235, 70 + (i % 4) * 30
        body += (
            f'<text x="{x}" y="{y}" font-size="14" fill="{TEXT}">{icon} {escape(label)}</text>'
            f'<text x="{x + 205}" y="{y}" font-size="14" font-weight="700" fill="{GREEN}" text-anchor="end">{escape(str(val))}</text>'
        )
    total = cc["contributionCalendar"]["totalContributions"]
    body += f'<text x="25" y="185" font-size="12" fill="{DIM}">{total} contributions in the last year</text>'
    return card(495, 200, "GITHUB STATS", body)


def langs_svg(u: dict) -> str:
    sizes = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            sizes[name] = (sizes.get(name, (0, None))[0] + e["size"], e["node"]["color"] or GREEN)
    top = sorted(sizes.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(s for _, (s, _) in top) or 1
    if not top:
        return card(350, 200, "TOP LANGUAGES", f'<text x="25" y="100" font-size="14" fill="{DIM}">No code in public repos yet: the journey begins!</text>')
    bar, x = "", 25.0
    for _, (s, color) in top:
        width = 300 * s / total
        bar += f'<rect x="{x:.1f}" y="55" width="{width:.1f}" height="10" fill="{color}"/>'
        x += width
    bar = f'<clipPath id="r"><rect x="25" y="55" width="300" height="10" rx="5"/></clipPath><g clip-path="url(#r)">{bar}</g>'
    items = ""
    for i, (name, (s, color)) in enumerate(top):
        x, y = 25 + (i % 2) * 155, 95 + (i // 2) * 30
        items += (
            f'<circle cx="{x + 5}" cy="{y - 5}" r="5" fill="{color}"/>'
            f'<text x="{x + 16}" y="{y}" font-size="13" fill="{TEXT}">{escape(name)} <tspan fill="{DIM}">{100 * s / total:.1f}%</tspan></text>'
        )
    return card(350, 200, "TOP LANGUAGES", bar + items)


def activity_svg(u: dict) -> str:
    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]][-31:]
    counts = [d["contributionCount"] for d in days]
    peak = -(-max(max(counts), 1) // 4) * 4  # round up to a multiple of 4 so the 5 grid ticks are whole numbers
    left, top, w, h = 50, 60, 800, 150
    pts = [(left + i * w / (len(counts) - 1 or 1), top + h - c * h / peak) for i, c in enumerate(counts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{left},{top + h} {line} {left + w},{top + h}"
    grid = "".join(
        f'<line x1="{left}" x2="{left + w}" y1="{top + h * k / 4}" y2="{top + h * k / 4}" stroke="{DIM}" stroke-opacity="0.2"/>'
        f'<text x="{left - 10}" y="{top + h * k / 4 + 4}" font-size="11" fill="{DIM}" text-anchor="end">{peak * (4 - k) // 4}</text>'
        for k in range(5)
    )
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{TEXT}"/>' for x, y in pts)
    labels = "".join(
        f'<text x="{pts[i][0]:.1f}" y="{top + h + 20}" font-size="11" fill="{DIM}" text-anchor="middle">{days[i]["date"][5:]}</text>'
        for i in range(0, len(days), 5)
    )
    body = (
        grid
        + f'<polygon points="{area}" fill="{GREEN}" fill-opacity="0.25"/>'
        + f'<polyline points="{line}" fill="none" stroke="{GREEN}" stroke-width="2"/>'
        + dots + labels
    )
    return card(880, 250, "CONTRIBUTIONS", body)


def main() -> None:
    login, out = sys.argv[1], sys.argv[2]
    u = fetch(login, os.environ["GITHUB_TOKEN"])
    os.makedirs(out, exist_ok=True)
    for name, svg in (("stats", stats_svg(u)), ("langs", langs_svg(u)), ("activity", activity_svg(u))):
        with open(os.path.join(out, f"{name}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)


if __name__ == "__main__":
    main()
