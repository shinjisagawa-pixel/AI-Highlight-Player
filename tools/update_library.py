import re
from pathlib import Path

REPO = Path(".")
TALKS_DIR = REPO / "talks"
INDEX_HTML = REPO / "index.html"
README = REPO / "README.md"

START = "<!-- AUTO-GENERATED TALKS START -->"
END = "<!-- AUTO-GENERATED TALKS END -->"

RT_START = "<!-- TALKS_TABLE_START -->"
RT_END = "<!-- TALKS_TABLE_END -->"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        t = t.replace("— Highlight Player", "").replace("– Highlight Player", "").strip()
        t = t.replace("— Highlighted Transcript Player", "").strip()
        return t
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        t = re.sub(r"<.*?>", "", m.group(1))
        t = re.sub(r"\s+", " ", t).strip()
        return t
    return "Untitled Talk"

def extract_duration_minutes(html: str) -> float:
    # parse segments = [{s:...,e:...}, ...] and use max e
    ends = re.findall(r"e\s*:\s*([0-9]+(?:\.[0-9]+)?)", html)
    if not ends:
        return 0.0
    max_end = max(float(x) for x in ends)
    return max_end / 60.0

def format_duration_tag(mins: float) -> str:
    # round to nearest 0.5 minutes, display like "~5 min" or "~5.5 min"
    if mins <= 0:
        return "~? min"
    rounded = round(mins * 2) / 2
    if rounded.is_integer():
        return f"~{int(rounded)} min"
    return f"~{rounded:.1f} min"

def created_from_slug(slug: str) -> str:
    # expects YYYY-MM-...
    m = re.match(r"(\d{4}-\d{2})-", slug)
    return m.group(1) if m else ""

def build_cards(talks):
    cards = []
    for t in talks:
        # relative link from root index.html
        href = f"./talks/{t['slug']}/"
        cards.append(f"""      <a class="card" href="{href}">
        <div><span class="tag">EN</span><span class="tag">{t['duration_tag']}</span></div>
        <div style="margin-top:10px;font-size:16px;font-weight:700;">
          {t['title']}
        </div>
        <div class="meta">Created: {t['created']} • Click to open <span class="go">→</span></div>
      </a>""")
    return "\n\n".join(cards) + "\n"

def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    if start_marker not in text or end_marker not in text:
        raise SystemExit(f"Missing markers: {start_marker} / {end_marker}")
    pre, rest = text.split(start_marker, 1)
    _, post = rest.split(end_marker, 1)
    return pre + start_marker + "\n" + replacement + "      " + end_marker + post

def build_readme_table(talks):
    lines = []
    lines.append("| # | Title | URL |")
    lines.append("|---:|---|---|")
    for i, t in enumerate(talks, 1):
        url = f"https://shinjisagawa-pixel.github.io/AI-Highlight-Player/talks/{t['slug']}/"
        lines.append(f"| {i} | {t['title']} | {url} |")
    return "\n".join(lines) + "\n"

def main():
    talks = []
    for p in sorted(TALKS_DIR.glob("*/index.html")):
        slug = p.parent.name
        html = read_text(p)
        title = extract_title(html)
        mins = extract_duration_minutes(html)
        talks.append({
            "slug": slug,
            "title": title,
            "duration_min": mins,
            "duration_tag": format_duration_tag(mins),
            "created": created_from_slug(slug) or "YYYY-MM",
        })

    # Keep newest first by slug (works if slug starts with YYYY-MM)
    talks = sorted(talks, key=lambda x: x["slug"], reverse=True)

    idx = read_text(INDEX_HTML)
    idx_new = replace_between(idx, START, END, build_cards(talks))
    write_text(INDEX_HTML, idx_new)

    rd = read_text(README)
    rd_new = replace_between(rd, RT_START, RT_END, build_readme_table(talks))
    write_text(README, rd_new)

    print("Updated index.html and README.md")

if __name__ == "__main__":
    main()
