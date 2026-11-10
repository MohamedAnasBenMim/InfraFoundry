import json
import tempfile
import time
from pathlib import Path

from .lab import HighAvailabilityLab


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        backup = Path(directory) / "backup.json"
        lab = HighAvailabilityLab()
        lab.nodes[0].content = "version-2026.11"
        manifest = lab.backup(backup)
        lab.fail("app-1")
        served_after_failure = lab.route()
        restore_started = time.perf_counter()
        restored = HighAvailabilityLab.restore(backup)
        restore_ms = (time.perf_counter() - restore_started) * 1000
        report = {"active_after_failover": lab.active.name, "served_after_failure": served_after_failure, "failover_ms": lab.failover_ms, "backup_checksum_verified": restored.nodes[0].content == "version-2026.11", "restore_ms": round(restore_ms, 4), "backup_checksum": manifest.checksum[:12]}
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/dr-report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
