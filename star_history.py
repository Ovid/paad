#!/usr/bin/env python3
"""Record a GitHub repository's star count over time and render it as SVG.

Standard library only. See docs/plans/2026-07-25-star-history-design.md.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone

DATA_DIR = ".github/star-history"
PROJECT_URL = "https://github.com/Ovid/star-history"
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")
SLUG_RE = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")

TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 1_000_000
API_ROOT = "https://api.github.com"

WIDTH, HEIGHT = 800, 400
CARD_HEIGHT = 150
PAD_L, PAD_R, PAD_T, PAD_B = 60, 20, 30, 50
PLOT_W = WIDTH - PAD_L - PAD_R
PLOT_H = HEIGHT - PAD_T - PAD_B

LINE_COLOR = "#e5533d"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
ATTRIBUTION = "github.com/Ovid/star-history"

THEMES = {
    "light": {"fg": "#24292f", "muted": "#57606a", "grid": "#d0d7de", "bg": "#ffffff"},
    "dark":  {"fg": "#c9d1d9", "muted": "#8b949e", "grid": "#30363d", "bg": None},
}


def load_history(path=HISTORY_PATH):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {"repo": None, "points": []}


def save_history(state, path=HISTORY_PATH):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def add_point(state, day, stars, src="snapshot"):
    """Insert a point for ISO date string `day`, replacing any point for that date.

    Mutates `state` in place. Sorting is lexicographic, which matches
    chronological order only because the dates are zero-padded ISO.
    """
    points = [p for p in state["points"] if p["date"] != day]
    points.append({"date": day, "stars": stars, "src": src})
    points.sort(key=lambda p: p["date"])
    state["points"] = points


def nice_step(maximum, target_ticks=5):
    """Smallest 1/2/5 x 10^k step giving about `target_ticks` gridlines."""
    raw = max(maximum, 1) / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiple in (1, 2, 5):
        step = multiple * magnitude
        # Ticks are integers; sub-decade repos truncate to 0 and floor to 1.
        if step >= raw:
            return max(1, int(step))
    return max(1, int(10 * magnitude))


def validate_slug(slug):
    """The one trust boundary: the slug goes straight into SVG text and API URLs."""
    if not SLUG_RE.fullmatch(slug or ""):
        sys.exit(f"not a valid OWNER/NAME repository slug: {slug!r}")
    return slug


def parse_remote(url):
    match = re.search(r"[:/]([A-Za-z0-9._-]+/[A-Za-z0-9._-]+?)(?:\.git)?/?$", url)
    return match.group(1) if match else None


def resolve_repo(explicit=None):
    """--repo flag, then $GITHUB_REPOSITORY, then the origin remote."""
    if explicit:
        return validate_slug(explicit)
    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return validate_slug(env)
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        url = ""
    slug = parse_remote(url)
    if not slug:
        sys.exit("cannot determine the repository; pass --repo OWNER/NAME")
    return validate_slug(slug)


def alt_text(state):
    """The accessibility surface: an SVG in an <img> exposes nothing else."""
    latest = state["points"][-1]
    return (f"Star history for {state['repo']}: {latest['stars']:,} "
            f"star{'' if latest['stars'] == 1 else 's'} as of {latest['date']}")


def _open(state, colors, slug, height):
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" role="img" aria-label="{alt_text(state)}">',
        f"<title>{alt_text(state)}</title>",
        f"<desc>Cumulative GitHub stars for {slug} over time.</desc>",
    ]
    if colors["bg"]:
        out.append(f'<rect width="{WIDTH}" height="{height}" fill="{colors["bg"]}"/>')
    return out


def _close(out, colors, slug, height, note=None):
    out.append(f'<rect x="{PAD_L}" y="10" width="10" height="10" fill="{LINE_COLOR}"/>')
    out.append(f'<text x="{PAD_L + 16}" y="19" font-family="{FONT}" font-size="13" '
               f'fill="{colors["fg"]}">{f"{slug} — {note}" if note else slug}</text>')
    out.append(f'<text x="{WIDTH - PAD_R}" y="{height - 10}" text-anchor="end" '
               f'font-family="{FONT}" font-size="11" '
               f'fill="{colors["muted"]}">{ATTRIBUTION}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _card(state, colors, slug):
    """Fewer than two points is not a time series. State the number instead of
    drawing a lone dot in the corner of an empty grid."""
    latest = state["points"][-1]
    count = latest["stars"]
    out = _open(state, colors, slug, CARD_HEIGHT)
    out.append(f'<text x="{PAD_L}" y="88" font-family="{FONT}" font-size="46" '
               f'font-weight="600" fill="{colors["fg"]}">{count:,}</text>')
    # 46px digits run about 28px wide; nudge the unit clear of the last one.
    out.append(f'<text x="{PAD_L + 28 * len(f"{count:,}") + 10}" y="88" '
               f'font-family="{FONT}" font-size="18" fill="{colors["muted"]}">'
               f'{"star" if count == 1 else "stars"}</text>')
    since = date.fromisoformat(state["points"][0]["date"])
    # A reconstructed count must never read as a measurement.
    lead = ("Reconstructed from GitHub timestamps as of"
            if latest["src"] == "backfill" else "Recording since")
    out.append(f'<text x="{PAD_L}" y="115" font-family="{FONT}" font-size="13" '
               f'fill="{colors["muted"]}">{lead} '
               f'{since.strftime("%b")} {since.day}, {since.year} — the chart '
               f'appears once there is history to draw.</text>')
    return _close(out, colors, slug, CARD_HEIGHT)


def _label_dates(points):
    """About six evenly spaced x labels; year shown only on long ranges."""
    span_days = (date.fromisoformat(points[-1]["date"]).toordinal()
                 - date.fromisoformat(points[0]["date"]).toordinal())
    fmt = "%b %Y" if span_days > 400 else "%b %d"
    count = min(6, len(points))
    step = max(1, (len(points) - 1) // max(1, count - 1)) if count > 1 else 1
    picked = points[::step]
    if picked[-1] is not points[-1]:
        picked.append(points[-1])
    labelled = {}  # text -> point; the last point wins so the right edge is labelled
    for point in picked:
        labelled[date.fromisoformat(point["date"]).strftime(fmt)] = point
    return [(point, text) for text, point in labelled.items()]


def render(state, theme):
    """Return a deterministic, self-contained SVG string for one theme."""
    colors = THEMES[theme]
    points = state["points"]
    if not points:
        raise ValueError("cannot render an empty history")

    slug = validate_slug(state["repo"])
    if len(points) < 2:
        return _card(state, colors, slug)

    ordinals = [date.fromisoformat(p["date"]).toordinal() for p in points]
    first, last = ordinals[0], ordinals[-1]
    span = max(1, last - first)
    peak = max(p["stars"] for p in points)
    step = nice_step(peak)
    top = max(step, math.ceil(peak / step) * step)

    def sx(ordinal):
        return PAD_L + round((ordinal - first) / span * PLOT_W)

    def sy(value):
        return PAD_T + round((1 - value / top) * PLOT_H)

    def polyline(subset):
        return " ".join(f"{sx(ordinals[i])},{sy(points[i]['stars'])}" for i in subset)

    backfill = [i for i, p in enumerate(points) if p["src"] == "backfill"]
    if backfill:
        cut = backfill[-1]
        dashed_idx = list(range(0, min(cut + 2, len(points))))
        solid_idx = list(range(cut + 1, len(points)))
    else:
        dashed_idx, solid_idx = [], list(range(len(points)))

    latest = points[-1]
    out = _open(state, colors, slug, HEIGHT)

    value = 0
    while value <= top:
        y = sy(value)
        out.append(f'<line x1="{PAD_L}" y1="{y}" x2="{PAD_L + PLOT_W}" y2="{y}" '
                   f'stroke="{colors["grid"]}" stroke-width="1"/>')
        out.append(f'<text x="{PAD_L - 8}" y="{y + 4}" text-anchor="end" '
                   f'font-family="{FONT}" font-size="12" '
                   f'fill="{colors["muted"]}">{value:,}</text>')
        value += step

    placed = []
    # Right to left, so the final date always gets its label and any neighbour
    # too close to it is the one dropped.
    for point, text in reversed(_label_dates(points)):
        # Centered text at the plot edge would clip; keep it inside the canvas.
        x = min(max(sx(date.fromisoformat(point["date"]).toordinal()), 32), WIDTH - 32)
        if placed and placed[-1] - x < 60:
            continue
        placed.append(x)
        out.append(f'<text x="{x}" y="{PAD_T + PLOT_H + 20}" text-anchor="middle" '
                   f'font-family="{FONT}" font-size="12" '
                   f'fill="{colors["muted"]}">{text}</text>')

    if len(dashed_idx) > 1:
        out.append(f'<polyline fill="none" stroke="{LINE_COLOR}" stroke-width="2" '
                   f'stroke-dasharray="5 4" points="{polyline(dashed_idx)}"/>')
    if len(solid_idx) > 1:
        out.append(f'<polyline fill="none" stroke="{LINE_COLOR}" stroke-width="2" '
                   f'points="{polyline(solid_idx)}"/>')
    out.append(f'<circle cx="{sx(last)}" cy="{sy(latest["stars"])}" r="3.5" '
               f'fill="{LINE_COLOR}"/>')

    return _close(out, colors, slug, HEIGHT,
                  "dashed is reconstructed" if backfill else None)


def render_all(state, data_dir=DATA_DIR):
    os.makedirs(data_dir, exist_ok=True)
    for theme in ("light", "dark"):
        with open(os.path.join(data_dir, f"{theme}.svg"), "w", encoding="utf-8") as handle:
            handle.write(render(state, theme))


def http_json(url, token=None, data=None, accept="application/vnd.github+json"):
    """One bounded, timed HTTP call. Any failure is fatal by design: a bad
    response must never be recorded as a data point."""
    headers = {"Accept": accept, "User-Agent": "star-history"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read(MAX_RESPONSE_BYTES))
    except urllib.error.HTTPError as error:
        # A private repo is indistinguishable from a missing one without a token.
        hint = ("; a private repository needs GITHUB_TOKEN"
                if error.code == 404 and not token else "")
        sys.exit(f"GitHub returned HTTP {error.code} for {url}{hint}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        sys.exit(f"could not reach GitHub: {error}")


def fetch_star_count(repo, token=None):
    payload = http_json(f"{API_ROOT}/repos/{repo}", token)
    if "stargazers_count" not in payload:
        sys.exit(f"no stargazers_count in the API response for {repo}")
    return int(payload["stargazers_count"])


GRAPHQL_URL = "https://api.github.com/graphql"
STARGAZER_QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    stargazerCount
    stargazers(first:100, after:$cursor,
               orderBy:{field:STARRED_AT, direction:ASC}) {
      pageInfo { hasNextPage endCursor }
      edges { starredAt }
    }
  }
}
"""


def cumulative_points(timestamps):
    """One point per day on which the star count changed."""
    running = 0
    per_day = {}
    for stamp in sorted(timestamps):
        running += 1
        per_day[stamp[:10]] = running
    return [{"date": day, "stars": total, "src": "backfill"}
            for day, total in sorted(per_day.items())]


def check_backfill_complete(collected, reported):
    if reported > 0 and collected == 0:
        sys.exit(
            "GitHub returned no star timestamps. Since 2026-06-30 these are "
            "restricted to repository admins and collaborators, and the API "
            "returns an empty list rather than an error. Backfill only works "
            "on repositories you own or help maintain; snapshot-only mode "
            "works everywhere."
        )
    if reported and abs(collected - reported) > max(5, reported * 0.01):
        sys.exit(f"only {collected} of {reported} stars retrieved; "
                 f"re-run backfill")


def merge_backfill(state, points):
    """Fill only dates the measured record does not already cover."""
    measured = {p["date"] for p in state["points"] if p["src"] == "snapshot"}
    earliest = min(measured) if measured else None
    for point in points:
        if point["date"] in measured:
            continue
        if earliest and point["date"] >= earliest:
            continue
        add_point(state, point["date"], point["stars"], src="backfill")


def backfill_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("no credentials: set GITHUB_TOKEN or run 'gh auth login'")


def fetch_star_timestamps(repo, token):
    owner, name = repo.split("/")
    cursor, stamps, reported = None, [], 0
    while True:
        payload = http_json(GRAPHQL_URL, token, data={
            "query": STARGAZER_QUERY,
            "variables": {"owner": owner, "name": name, "cursor": cursor}})
        if "errors" in payload:
            sys.exit(f"GraphQL error: {payload['errors']}")
        node = payload["data"]["repository"]["stargazers"]
        reported = payload["data"]["repository"]["stargazerCount"]
        stamps.extend(edge["starredAt"] for edge in node["edges"])
        print(f"  {len(stamps)}/{reported}", file=sys.stderr)
        if not node["pageInfo"]["hasNextPage"]:
            return stamps, reported
        cursor = node["pageInfo"]["endCursor"]


def cmd_backfill(args):
    data_dir = args.data_dir or DATA_DIR
    path = os.path.join(data_dir, "history.json")
    repo = resolve_repo(args.repo)
    state = load_history(path)
    if any(p["src"] == "backfill" for p in state["points"]) and not args.force:
        sys.exit("history already contains backfilled points; pass --force")
    stamps, reported = fetch_star_timestamps(repo, backfill_token())
    check_backfill_complete(len(stamps), reported)
    state["repo"] = repo
    merge_backfill(state, cumulative_points(stamps))
    save_history(state, path)
    render_all(state, data_dir)
    print(f"{repo}: backfilled {len(stamps)} stars")


def today_utc():
    return datetime.now(timezone.utc).date().isoformat()


def snippet_block(state, data_dir=DATA_DIR):
    alt = alt_text(state)
    return (
        f'<a href="{PROJECT_URL}">\n'
        f"  <picture>\n"
        f'    <source media="(prefers-color-scheme: dark)"  srcset="{data_dir}/dark.svg">\n'
        f'    <source media="(prefers-color-scheme: light)" srcset="{data_dir}/light.svg">\n'
        f'    <img alt="{alt}" src="{data_dir}/light.svg" width="800">\n'
        f"  </picture>\n"
        f"</a>\n"
    )


def cmd_update(args):
    data_dir = args.data_dir or DATA_DIR
    path = os.path.join(data_dir, "history.json")
    repo = resolve_repo(args.repo)
    state = load_history(path)
    if state.get("repo") and state["repo"] != repo:
        print(f"note: repository renamed {state['repo']} -> {repo}", file=sys.stderr)
    state["repo"] = repo
    count = fetch_star_count(repo, os.environ.get("GITHUB_TOKEN"))
    add_point(state, today_utc(), count)
    save_history(state, path)
    render_all(state, data_dir)
    print(f"{repo}: {count} stars, {len(state['points'])} points")


def cmd_snippet(args):
    data_dir = args.data_dir or DATA_DIR
    state = load_history(os.path.join(data_dir, "history.json"))
    if not state["points"]:
        sys.exit("no history yet — run the workflow once, then try again")
    print(snippet_block(state, data_dir))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="OWNER/NAME (default: env or git remote)")
    parser.add_argument("--data-dir", default=DATA_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("update", help="record today's count and render")
    sub.add_parser("snippet", help="print the README block")
    backfill = sub.add_parser("backfill", help="one-time local history rebuild")
    backfill.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    {"update": cmd_update, "snippet": cmd_snippet,
     "backfill": cmd_backfill}[args.command](args)


if __name__ == "__main__":
    main()
