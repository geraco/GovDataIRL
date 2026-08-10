"""Report builder — renders Jinja2 templates to static HTML, updates the
archive index, JSON feed and RSS feed. No server-side rendering at request
time (spec §5.6)."""
import json
import re
import uuid
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader

from config import ACCENT_COLOUR, SITE_OUT, SITE_TITLE
from db.store import connect, upsert

TEMPLATES_DIR = SITE_OUT.parent / "rendering" / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def _unique_slug(base_slug: str) -> str:
    """Same title can recur same-day (different resource under one package,
    or a re-run) — disambiguate rather than crash on the UNIQUE constraint."""
    with connect() as conn:
        existing = {r["slug"] for r in conn.execute("SELECT slug FROM reports")}
    if base_slug not in existing:
        return base_slug
    n = 2
    while f"{base_slug}-{n}" in existing:
        n += 1
    return f"{base_slug}-{n}"


def build_report(pipeline_result: dict, source_notes: dict, chart_tags: list[str],
                  dataset_title: str, dataset_page_url: str, interestingness_score: int,
                  resource_id: str, data_period: str | None = None) -> dict:
    narrative = pipeline_result["narrative"]
    now = datetime.now(timezone.utc)
    slug = _unique_slug(f"{now.strftime('%Y-%m-%d')}-{_slugify(dataset_title)}")

    report = {
        "report_id": uuid.uuid4().hex,
        "resource_id": resource_id,
        "slug": slug,
        "dataset_title": dataset_title,
        "dataset_page_url": dataset_page_url,
        "publisher": source_notes["publisher"],
        "licence": source_notes["licence"],
        "last_updated": source_notes["last_updated"] or "unknown",
        "data_period": data_period,
        "source_url": source_notes["url"],
        "interestingness_score": interestingness_score,
        "narrative": narrative,
        "chart_tags": chart_tags,
        "published_at": now.isoformat(),
    }

    css = env.get_template("base.css").render(accent=ACCENT_COLOUR)
    html = env.get_template("report.html").render(report=report, site_title=SITE_TITLE, css=css)

    reports_dir = SITE_OUT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    html_path = reports_dir / f"{slug}.html"
    html_path.write_text(html, encoding="utf-8")

    with connect() as conn:
        upsert(conn, "reports", {
            "report_id": report["report_id"], "resource_id": resource_id, "slug": slug,
            "headline": narrative["headline"], "teaser": narrative["headline"],
            "publisher": source_notes["publisher"], "published_at": report["published_at"],
            "narrative_json": json.dumps(pipeline_result, default=str),
            "html_path": str(html_path),
            "interestingness_score": interestingness_score,
            "dataset_last_updated": source_notes["last_updated"] or None,
        })

    rebuild_index()
    return report


def _conf_dots(score) -> int:
    """Maps the real interestingness score (0-100) onto a 1-5 dot indicator."""
    if score is None:
        return 0
    return max(1, min(5, round(score / 20)))


def _freshness(dataset_last_updated: str | None, now: datetime) -> tuple[int | None, str]:
    """Days since the source dataset itself was last modified (per CKAN
    metadata) — a real staleness signal, not a fabricated one."""
    if not dataset_last_updated:
        return None, ""
    try:
        updated = datetime.fromisoformat(dataset_last_updated.replace("Z", "+00:00"))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
    except ValueError:
        return None, ""
    days = max(0, (now - updated).days)
    cls = "fresh" if days <= 1 else ("aging" if days <= 7 else "stale")
    return days, cls


def rebuild_index():
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM reports ORDER BY published_at DESC"
        )]

    now = datetime.now(timezone.utc)
    for r in rows:
        r["published_at_date"] = r["published_at"][:10]
        r["conf_dots"] = _conf_dots(r.get("interestingness_score"))
        r["freshness_days"], r["freshness_class"] = _freshness(r.get("dataset_last_updated"), now)

    agency_counts = {}
    for r in rows:
        agency_counts[r["publisher"]] = agency_counts.get(r["publisher"], 0) + 1
    agencies = [{"name": name, "count": count} for name, count in agency_counts.items()]

    css = env.get_template("base.css").render(accent=ACCENT_COLOUR)
    html = env.get_template("index.html").render(
        reports=rows, agencies=agencies, site_title=SITE_TITLE, css=css,
        last_run_at=rows[0]["published_at"][:16].replace("T", " ") + " UTC" if rows else None,
    )
    SITE_OUT.mkdir(parents=True, exist_ok=True)
    (SITE_OUT / "index.html").write_text(html, encoding="utf-8")

    (SITE_OUT / "feed.json").write_text(json.dumps({
        "version": "https://jsonfeed.org/version/1.1",
        "title": SITE_TITLE,
        "items": [
            {"id": r["report_id"], "title": r["headline"], "summary": r["teaser"],
             "url": f"reports/{r['slug']}.html", "date_published": r["published_at"]}
            for r in rows
        ],
    }, indent=2), encoding="utf-8")

    items_xml = "\n".join(
        f"<item><title>{xml_escape(r['headline'])}</title>"
        f"<link>reports/{r['slug']}.html</link>"
        f"<description>{xml_escape(r['teaser'])}</description>"
        f"<pubDate>{r['published_at']}</pubDate></item>"
        for r in rows
    )
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{xml_escape(SITE_TITLE)}</title>{items_xml}</channel></rss>"
    )
    (SITE_OUT / "feed.xml").write_text(rss, encoding="utf-8")
