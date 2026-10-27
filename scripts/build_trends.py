#!/usr/bin/env python3
"""Build trend data for the Plastic Signal Weekly dashboard.

Parses every published weekly issue (Jekyll posts with `newsletter: plastics`
and a per-item structure) and writes one JSON file that docs/trends.html reads.

Usage:
    python scripts/build_trends.py --posts docs/_posts --out docs/data/trends.json

Pass --posts more than once to merge several folders (e.g. the gh-pages
history plus the issue built in the current run). Later folders win when the
same file name appears twice.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ITEM_ANCHOR = re.compile(r'<a id="item-([a-z0-9-]+?)-(\d+)"></a>')
HEADING = re.compile(r"^###\s+\[(?P<title>.+?)\]\((?P<url>[^)\s]+)\)\s*(?:⭐️\s*(?P<score>[\d.]+)/10)?", re.M)
SOURCE_LINE = re.compile(r"^(?P<kind>[a-z_]+)\s+·\s+(?P<source>.+?)\s+·\s+(?P<when>[A-Z][a-z]{2} \d{1,2}(?:, \d{1,2}:\d{2})?)\s*$", re.M)
TAGS_LINE = re.compile(r"^\*\*Tags\*\*:\s*(?P<tags>.+)$", re.M)
LABELLED = re.compile(r"^\*\*「(?P<label>[^」]+)」\*\*\s*(?P<text>.+)$", re.M)
SIGNALS_LINE = re.compile(r"^>\s*From\s+(?P<seen>\d+)\s+signals,\s+(?P<kept>\d+)", re.M)

# Section slug -> display name. Matches the eight pillars from Issue 00.
PILLARS = {
    "market-business": "Market & Business",
    "sustainable-materials": "Sustainable Materials",
    "recycling-tech": "Recycling Technologies",
    "supply-chain": "Supply Chain & Feedstock",
    "regulation-compliance": "Regulations & Compliance",
    "research-patents": "Research & Patents",
    "material-performance": "Material Performance",
    "future-materials": "Future Materials",
}

# The "next action" verb is the newsletter's own call to action: track, verify,
# sample, test or qualify. Map the wording the model uses onto those buckets.
ACTION_BUCKETS = [
    ("Track", ("track", "monitor", "watch", "follow")),
    ("Request evidence", ("request", "ask", "obtain", "retrieve", "pull", "locate", "get")),
    ("Verify", ("check", "confirm", "verify", "audit", "validate", "cross-check")),
    ("Test / sample", ("test", "sample", "trial", "pilot", "benchmark")),
    ("Qualify / decide", ("qualify", "assess", "evaluate", "screen", "decide", "prepare", "model", "if")),
]

# Light normalisation so the same idea is counted once.
TAG_ALIASES = {
    "pe": "polyethylene",
    "pp": "polypropylene",
    "pet": "PET",
    "rpet": "rPET",
    "hdpe": "HDPE",
    "ldpe": "LDPE",
    "pvc": "PVC",
    "pha": "PHA",
    "pla": "PLA",
    "epr": "EPR",
    "extended producer responsibility": "EPR",
    "ppwr": "PPWR",
    "eu": "EU",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "uk": "UK",
    "north america": "North America",
    "m&a": "M&A",
    "mergers and acquisitions": "M&A",
    "acquisition": "M&A",
    "chemical recycling": "chemical recycling",
    "advanced recycling": "chemical recycling",
    "mechanical recycling": "mechanical recycling",
    "recycled content": "recycled content",
    "pcr": "recycled content",
    "post-consumer resin": "recycled content",
    "bioplastics": "bioplastics",
    "bio-based plastics": "bioplastics",
    "biobased": "bioplastics",
}

# Curated lenses. Free-form AI tags are too scattered to trend on their own
# (hundreds of spellings for ~90 items), so each item is also matched against
# these fixed themes using its title, summary and tags. Edit freely.
THEMES = {
    "Polymer": {
        "Polyethylene (PE/HDPE/LDPE)": r"\b(polyethylene|r?hdpe|r?ldpe|lldpe|r?pe)\b",
        "Polypropylene (PP)": r"\b(polypropylene|r?pp)\b",
        "PET / polyester": r"\b(r?pet|polyester|petg)\b",
        "PVC": r"\bpvc\b",
        "Bio-based & biodegradable": r"\b(pha|pla|bio-?based|bioplastic\w*|biodegrad\w*|compostab\w*|biopolymer\w*)\b",
        "Engineering & high-performance": r"\b(pps|peek|polyamide|nylon|pa6|pa66|engineered (?:plastics|thermoplastics)|engineering plastics?|thermoplastic composites?|polycarbonate|(?-i:ABS))\b",
    },
    "Driver": {
        "EPR & packaging law": r"\b(epr|producer responsibility|ppwr|sb 54|packaging (?:law|decree|regulation)|(?-i:PROs?)\b|single-use)",
        "Trade, tariffs & duties": r"\b(tariff\w*|anti-?dumping|section 301|ustr|trade (?:remed\w*|defen[cs]e)|imports?)\b",
        "Resin prices & feedstock": r"\b(pric\w+|feedstock|ethane|naphtha|inventor(?:y|ies)|spot)\b",
        "Capacity moves & investment": r"\b(capacity|invest(?:s|ed|ing|ment)?|new (?:plant|facility|line|site)|expansion|expands?|breaks? ground|opens? (?:an? |its |new )?[\w-]* ?(?:plant|site|facility|cent(?:er|re)|line)|start-?up)\b",
        "M&A & partnerships": r"\b(acquir(?:e|es|ed|ing)|acquisition|merger|m&a|buys?|buyout|joint venture|partner(?:s|ship\w*|ing|ed)?)\b",
        "Recycled content & claims": r"\b(recycled content|pcr|post-consumer|100% recycled|claims?|greenwash\w*)\b",
        "Mechanical recycling": r"\bmechanical(?:ly)? recycl\w*|\bgranulat\w*|\bwash(?:ing)? line",
        "Chemical & enzymatic recycling": r"\b(chemical recycl\w*|advanced recycl\w*|pyrolysis|depolymeri\w+|solvent-based|enzym\w+|dissolution)\b",
        "Bans & chemical restrictions": r"\b(bans?|banned|banning|microplastic\w*|hazardous|candidate chemicals?|safer consumer products|restrict\w*|pfas)\b",
        "Medical & healthcare": r"\b(medical|healthcare|sterile|pharma\w*)\b",
        "Automotive & EV": r"\b(automotive|ev|electric vehicle|car|vehicle)\b",
        "Textiles": r"\b(textile\w*|fibre|fiber|apparel)\b",
        "AI & digital": r"\b(ai|machine vision|digital\w*|software|sensor\w*)\b",
    },
}

REGIONS = {
    "United States": r"\b((?-i:U\.?S\.?A?)|united[- ]states|american?|california|maine|oregon|colorado|new york|texas|missouri|iowa|pennsylvania|georgia|michigan|nevada|wisconsin|north carolina|ohio|virginia|baltimore|washington state|newsom)\b",
    "Canada": r"\b(canada|canadian|ontario|waterloo|quebec)\b",
    "Mexico & Latin America": r"\b(mexico|mexican|monterrey|brazil\w*|colombia\w*|andean|chile|argentina|latin america)\b",
    "European Union": r"\b(eu|european union|europe|european commission|horizon europe)\b",
    "Germany": r"\b(german\w*|fakuma)\b",
    "Italy": r"\b(ital\w*|modena)\b",
    "France": r"\b(france|french|carbios)\b",
    "UK": r"\b(uk|united kingdom|britain|british|england)\b",
    "Nordics": r"\b(sweden|swedish|norway|finland|denmark|nordic\w*)\b",
    "Other Europe": r"\b(spain|netherlands|dutch|belgium|austria|poland|slovenia|ukrain\w*|switzerland)\b",
    "China": r"\b(china|chinese)\b",
    "India & South Asia": r"\b(india\w*|nepal\w*|bangladesh|pakistan)\b",
    "Japan & Korea": r"\b(japan\w*|korea\w*|toray)\b",
    "Middle East": r"\b(uae|saudi|borouge|middle east|qatar)\b",
    "Australia & NZ": r"\b(australia\w*|new zealand|aldi australia)\b",
}

REGION_TAGS = {
    "EU", "Europe", "US", "North America", "UK", "China", "India", "Japan", "Korea", "South Korea",
    "Germany", "France", "Italy", "Spain", "Netherlands", "Australia", "Canada", "Brazil", "Mexico",
    "Asia", "Southeast Asia", "Middle East", "Africa", "Latin America", "Ukraine", "Sweden", "Nordics",
    "California", "Maine", "Oregon", "Colorado", "New York", "Texas", "Missouri", "Iowa", "Pennsylvania",
}
US_STATES = {"California", "Maine", "Oregon", "Colorado", "New York", "Texas", "Missouri", "Iowa", "Pennsylvania"}


_COMPILED: dict[int, list] = {}


def match_all(table: dict, text: str) -> list[str]:
    """Return every key in `table` (flat or grouped) whose pattern matches text."""
    key = id(table)
    if key not in _COMPILED:
        flat = []
        for k, v in table.items():
            if isinstance(v, dict):
                flat += [(f"{k}: {n}", re.compile(p, re.I)) for n, p in v.items()]
            else:
                flat.append((k, re.compile(v, re.I)))
        _COMPILED[key] = flat
    text = html.unescape(text)
    return [name for name, rx in _COMPILED[key] if rx.search(text)]


def front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 4 :]


def clean(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


PILLAR_TAG_NOISE = {"market-business", "regulation-compliance", "sustainable-materials", "recycling-tech",
                    "supply-chain", "research-patents", "material-performance", "future-materials"}


def norm_tag(raw: str) -> str:
    tag = clean(raw.strip().strip("`").lstrip("#")).replace("moulding", "molding")
    if tag.lower() in PILLAR_TAG_NOISE:
        return ""
    tag = tag.replace("-", " ") if not re.search(r"[A-Z]{2}", tag) else tag
    key = tag.lower()
    if key in TAG_ALIASES:
        return TAG_ALIASES[key]
    # Keep acronyms and proper nouns as written, lowercase everything else.
    if tag.isupper() or any(w[:1].isupper() for w in tag.split()[1:]) or tag in REGION_TAGS:
        return tag
    return tag[:1].lower() + tag[1:] if not tag[:2].isupper() else tag


def action_bucket(text: str) -> str:
    first = re.sub(r"[^a-z\- ]", "", text.lower()).split()
    first = first[0] if first else ""
    for name, verbs in ACTION_BUCKETS:
        if first in verbs:
            return name
    return "Other"


def parse_issue(path: Path) -> dict | None:
    meta, body = front_matter(path.read_text(encoding="utf-8"))
    if meta.get("newsletter") != "plastics" or meta.get("lang", "en") != "en":
        return None
    anchors = list(ITEM_ANCHOR.finditer(body))
    if not anchors:
        return None  # editorial issues such as Issue 00

    issue_date = meta.get("date") or path.name[:10]
    year = int(issue_date[:4])
    signals = SIGNALS_LINE.search(body)
    items = []
    for i, anchor in enumerate(anchors):
        chunk = body[anchor.end() : anchors[i + 1].start() if i + 1 < len(anchors) else len(body)]
        head = HEADING.search(chunk)
        if not head:
            continue
        after = chunk[head.end():].strip().split("\n\n", 1)[0]
        summary = clean(after) if not SOURCE_LINE.match(after) else ""
        pillar = anchor.group(1)
        src = SOURCE_LINE.search(chunk)
        tags_m = TAGS_LINE.search(chunk)
        tags = []
        if tags_m:
            seen = set()
            for raw in tags_m.group("tags").split(","):
                t = norm_tag(raw)
                if t and t.lower() not in seen:
                    seen.add(t.lower())
                    tags.append(t)
        labelled = {m.group("label").strip().lower(): clean(m.group("text")) for m in LABELLED.finditer(chunk)}
        next_action = labelled.get("next action") or labelled.get("next step") or ""
        published = None
        if src:
            try:
                d = datetime.strptime(f"{src.group('when').split(',')[0]} {year}", "%b %d %Y").date()
                if d > date.fromisoformat(issue_date):  # December item in a January issue
                    d = d.replace(year=year - 1)
                published = d.isoformat()
            except ValueError:
                pass
        items.append(
            {
                "issue": issue_date,
                "pillar": pillar,
                "pillar_name": PILLARS.get(pillar, pillar.replace("-", " ").title()),
                "rank": int(anchor.group(2)),
                "title": clean(head.group("title")),
                "url": head.group("url"),
                "score": float(head.group("score")) if head.group("score") else None,
                "channel": src.group("kind") if src else None,
                "source": clean(src.group("source")).split(" — ")[0] if src else None,
                "published": published,
                "summary": summary,
                "tags": tags,
                "themes": match_all(THEMES, " ".join([head.group("title"), summary, " ".join(tags)])),
                "regions": match_all(REGIONS, " ".join([head.group("title"), summary, " ".join(tags)])),
                "next_action": next_action,
                "action": action_bucket(next_action) if next_action else None,
            }
        )
    return {
        "date": issue_date,
        "title": meta.get("title", ""),
        "url": f"{issue_date[:4]}/{issue_date[5:7]}/{issue_date[8:10]}/{path.stem[11:]}.html",
        "signals_seen": int(signals.group("seen")) if signals else None,
        "items_kept": len(items),
        "items": items,
    }


def momentum(counts_by_week: dict[str, Counter], weeks: list[str], window: int = 2) -> list[dict]:
    """Compare mention share in the latest `window` issues with the issues before."""
    if len(weeks) < window + 1:
        return []
    recent, earlier = weeks[-window:], weeks[:-window]
    totals = {w: sum(counts_by_week[w].values()) or 1 for w in weeks}
    rows = []
    names = set().union(*(counts_by_week[w].keys() for w in weeks))
    for name in sorted(names):
        r = sum(counts_by_week[w][name] for w in recent)
        e = sum(counts_by_week[w][name] for w in earlier)
        if r + e < 2:
            continue
        r_share = r / sum(totals[w] for w in recent)
        e_share = e / sum(totals[w] for w in earlier)
        rows.append({"name": name, "recent": r, "earlier": e, "delta": round(r_share - e_share, 4)})
    rows.sort(key=lambda x: (-x["delta"], -x["recent"], x["name"]))
    return rows


def build(post_dirs: list[Path]) -> dict:
    files: dict[str, Path] = {}
    for d in post_dirs:
        for p in sorted(d.glob("*.md")):
            files[p.name] = p
    issues = [i for i in (parse_issue(p) for _, p in sorted(files.items())) if i]
    issues.sort(key=lambda i: i["date"])
    weeks = [i["date"] for i in issues]
    items = [it for i in issues for it in i["items"]]

    pillar_week = {w: Counter() for w in weeks}
    tag_week = {w: Counter() for w in weeks}
    region_week = {w: Counter() for w in weeks}
    theme_week = {w: Counter() for w in weeks}
    for it in items:
        pillar_week[it["issue"]][it["pillar_name"]] += 1
        for t in it["tags"]:
            if t not in REGION_TAGS:
                tag_week[it["issue"]][t] += 1
        for r in it["regions"]:
            region_week[it["issue"]][r] += 1
        for th in it["themes"]:
            theme_week[it["issue"]][th] += 1

    def theme_rows(group: str) -> list[dict]:
        rows = []
        for name in THEMES[group]:
            key = f"{group}: {name}"
            by_week = [theme_week[w][key] for w in weeks]
            hits = [it for it in items if key in it["themes"]]
            if not hits:
                continue
            sc = [it["score"] for it in hits if it["score"] is not None]
            rows.append({
                "name": name,
                "count": len(hits),
                "by_week": by_week,
                "avg_score": round(sum(sc) / len(sc), 2) if sc else None,
                "share": round(len(hits) / max(len(items), 1), 3),
            })
        rows.sort(key=lambda r: -r["count"])
        return rows

    tag_total = Counter()
    tag_issues = defaultdict(set)
    for w in weeks:
        tag_total.update(tag_week[w])
        for t in tag_week[w]:
            tag_issues[t].add(w)
    top_tags = [
        {"name": t, "count": c, "issues": len(tag_issues[t]), "by_week": [tag_week[w][t] for w in weeks]}
        for t, c in tag_total.most_common(25)
    ]

    pillar_order = [p for p in PILLARS.values() if any(pillar_week[w][p] for w in weeks)]
    pillar_series = [{"name": p, "by_week": [pillar_week[w][p] for w in weeks]} for p in pillar_order]

    region_rollup = Counter()
    for w in weeks:
        region_rollup.update(region_week[w])
    theme_mom = {g: [] for g in THEMES}
    for row in momentum(theme_week, weeks):
        g, n = row["name"].split(": ", 1)
        theme_mom[g].append({**row, "name": n})

    source_total = Counter(it["source"] for it in items if it["source"])
    action_total = Counter(it["action"] for it in items if it["action"])

    scores = [it["score"] for it in items if it["score"] is not None]
    high = sorted((it for it in items if (it["score"] or 0) >= 6), key=lambda x: (-x["score"], x["issue"]))

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weeks": weeks,
        "issues": [{k: v for k, v in i.items() if k != "items"} for i in issues],
        "totals": {
            "issues": len(issues),
            "items": len(items),
            "signals_seen": sum(i["signals_seen"] or 0 for i in issues),
            "sources": len(source_total),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
            "high_signal": len(high),
        },
        "pillars": pillar_series,
        "polymers": theme_rows("Polymer"),
        "drivers": theme_rows("Driver"),
        "theme_momentum": theme_mom,
        "top_tags": top_tags,
        "rising_tags": momentum(tag_week, weeks)[:10],
        "cooling_tags": sorted(momentum(tag_week, weeks), key=lambda x: x["delta"])[:6],
        "pillar_momentum": momentum(pillar_week, weeks),
        "regions": [{"name": r, "count": c, "by_week": [region_week[w][r] for w in weeks]} for r, c in region_rollup.most_common(12)],
        "sources": [{"name": s, "count": c} for s, c in source_total.most_common(12)],
        "actions": [{"name": a, "count": c} for a, c in action_total.most_common()],
        "high_signal": high,
        "items": items,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--posts", action="append", type=Path, required=True, help="folder of Jekyll posts (repeatable)")
    ap.add_argument("--out", type=Path, required=True, help="output JSON path")
    args = ap.parse_args()
    data = build([p for p in args.posts if p.exists()])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    t = data["totals"]
    print(f"trends: {t['issues']} issues, {t['items']} items, {len(data['top_tags'])} top tags -> {args.out}")


if __name__ == "__main__":
    main()
