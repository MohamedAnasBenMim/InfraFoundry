from pathlib import Path

from infrafoundry.lab import HighAvailabilityLab


def test_service_fails_over_to_healthy_node() -> None:
    lab = HighAvailabilityLab()
    lab.fail("app-1")
    assert lab.route() == "service-ready"
    assert lab.active.name == "app-2"
    assert lab.failover_ms is not None


def test_all_nodes_down_returns_error() -> None:
    lab = HighAvailabilityLab()
    lab.fail("app-1")
    lab.fail("app-2")
    try:
        lab.route()
    except RuntimeError as error:
        assert "no healthy" in str(error)
    else:
        raise AssertionError("an unavailable cluster must fail")


def test_backup_and_restore_preserve_service_data(tmp_path: Path) -> None:
    lab = HighAvailabilityLab()
    lab.nodes[0].content = "release-42"
    backup = tmp_path / "backup.json"
    manifest = lab.backup(backup)
    restored = HighAvailabilityLab.restore(backup)
    assert restored.nodes[0].content == "release-42"
    assert manifest.nodes == 2


def test_tampered_backup_is_rejected(tmp_path: Path) -> None:
    backup = tmp_path / "backup.json"
    HighAvailabilityLab().backup(backup)
    backup.write_text(backup.read_text().replace("service-ready", "tampered"))
    try:
        HighAvailabilityLab.restore(backup)
    except ValueError as error:
        assert "checksum" in str(error)
    else:
        raise AssertionError("tampered backups must fail")


def test_manual_failover_selects_first_healthy_node() -> None:
    lab = HighAvailabilityLab()
    lab.active_index = 1
    assert lab.failover().name == "app-1"
