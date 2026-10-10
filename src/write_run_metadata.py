"""Record a successful GitHub Actions report run without storing credentials."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def main(output_path: Path) -> None:
    now = datetime.now(timezone.utc)
    run_url = (
        f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
        f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    )
    metadata = {
        "date_vietnam": now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat(),
        "report_sent_at_utc": now.isoformat(timespec="seconds"),
        "workflow_run_url": run_url,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
