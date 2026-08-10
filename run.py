"""Entry point: discover -> analyse -> publish. Spec §4 / §10.

    python run.py               # normal run: refresh pool, pick, publish
    python run.py --no-refresh  # skip the pool refresh (use cached candidates)
"""
import sys
import uuid
from datetime import datetime, timezone

from analyst import run_pipeline
from connectors import NotNarrable, fetch as connector_fetch
from db.store import connect, init_db, upsert
from discovery.discover import pick_dataset, refresh_candidate_pool
from profiling.insights import detect_insights
from profiling.profiler import data_period_label, profile_dataframe
from publish.build_site import build_report
from publish.notify import notify_published
from rendering.charts import render_all


def _log_run(resource_id, status, failure_reason=None, published_report_id=None):
    with connect() as conn:
        upsert(conn, "runs", {
            "run_id": uuid.uuid4().hex,
            "resource_id": resource_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "failure_reason": failure_reason,
            "published_report_id": published_report_id,
        })


def _try_publish(candidate: dict) -> bool:
    """Returns True on success. Never raises — caller decides whether to re-roll."""
    resource = {"id": candidate["resource_id"], "url": candidate["resource_url"],
                "format": candidate["resource_format"], "datastore_active": candidate["shape"] == "datastore"}
    package = {"id": candidate["package_id"], "title": candidate["title"],
               "license_title": candidate["licence"],
               "metadata_modified": candidate["package_last_modified"],
               "organization": {"title": candidate["publisher"]}}

    try:
        df, source_notes = connector_fetch(resource, package)
        profile = profile_dataframe(df)
        insights = detect_insights(df, profile)
        metadata = {
            "title": candidate["title"], "publisher": candidate["publisher"],
            "licence": candidate["licence"], "description": candidate["package_notes"],
        }
        pipeline_result = run_pipeline(metadata, profile, insights, df)
        chart_tags = render_all(pipeline_result["chart_specs"])
        dataset_page_url = f"https://data.gov.ie/dataset/{candidate['package_name']}"

        report = build_report(
            pipeline_result, source_notes, chart_tags,
            dataset_title=candidate["title"], dataset_page_url=dataset_page_url,
            interestingness_score=candidate["interestingness_score"],
            resource_id=candidate["resource_id"],
            data_period=data_period_label(profile),
        )
        _log_run(candidate["resource_id"], "success", published_report_id=report["report_id"])
        notify_published(report)
        return True
    except (NotNarrable, RuntimeError, ValueError) as e:
        _log_run(candidate["resource_id"], "failed", failure_reason=str(e))
        print(f"[run] failed on {candidate['title']}: {e}")
        return False


def main():
    init_db()

    if "--no-refresh" not in sys.argv:
        print("[run] refreshing candidate pool...")
        refresh_candidate_pool()

    candidate = pick_dataset()
    if candidate is None:
        print("[run] no viable candidates in the pool — nothing to publish")
        return

    print(f"[run] picked: {candidate['title']} (score {candidate['interestingness_score']})")
    if _try_publish(candidate):
        print("[run] done.")
        return

    print("[run] re-rolling once...")
    reroll = pick_dataset()
    if reroll is None or reroll["resource_id"] == candidate["resource_id"]:
        print("[run] no alternative candidate available — skipping this run")
        return

    if _try_publish(reroll):
        print("[run] done (after re-roll).")
    else:
        print("[run] re-roll also failed — skipping this run, no broken report published")


if __name__ == "__main__":
    main()
