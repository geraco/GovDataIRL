"""ntfy push on publish. Deploy itself is handled by the GitHub Actions
workflow (.github/workflows/publish.yml), which commits docs/ and lets
GitHub Pages branch-serve it — nothing to do here beyond the notification."""
import httpx

from config import NTFY_TOPIC


def notify_published(report: dict):
    if not NTFY_TOPIC:
        print(f"[notify] skipped (NTFY_TOPIC unset) — would have sent: New data story: {report['narrative']['headline']}")
        return
    httpx.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=f"New data story: {report['narrative']['headline']}".encode(),
        headers={"Click": f"reports/{report['slug']}.html"},
        timeout=10,
    )
