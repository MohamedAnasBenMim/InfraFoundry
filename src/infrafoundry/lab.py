from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class ServiceNode:
    name: str
    healthy: bool = True
    content: str = "service-ready"


@dataclass(frozen=True, slots=True)
class BackupManifest:
    created_at_ns: int
    checksum: str
    nodes: int


class HighAvailabilityLab:
    def __init__(self, nodes: list[ServiceNode] | None = None) -> None:
        self.nodes = nodes or [ServiceNode("app-1"), ServiceNode("app-2")]
        self.active_index = 0
        self.failover_ms: float | None = None

    @property
    def active(self) -> ServiceNode:
        return self.nodes[self.active_index]

    def route(self) -> str:
        if not self.active.healthy:
            self.failover()
        if not self.active.healthy:
            raise RuntimeError("no healthy backend")
        return self.active.content

    def fail(self, node_name: str) -> None:
        next(node for node in self.nodes if node.name == node_name).healthy = False

    def failover(self) -> ServiceNode:
        started = time.perf_counter()
        for index, node in enumerate(self.nodes):
            if node.healthy:
                self.active_index = index
                self.failover_ms = round((time.perf_counter() - started) * 1000, 4)
                return node
        self.failover_ms = round((time.perf_counter() - started) * 1000, 4)
        return self.active

    def backup(self, path: Path) -> BackupManifest:
        payload = json.dumps([asdict(node) for node in self.nodes], sort_keys=True)
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        manifest = BackupManifest(time.time_ns(), checksum, len(self.nodes))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"manifest": asdict(manifest), "payload": payload}, indent=2) + "\n", encoding="utf-8")
        return manifest

    @classmethod
    def restore(cls, path: Path) -> HighAvailabilityLab:
        backup = json.loads(path.read_text(encoding="utf-8"))
        payload = backup["payload"]
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        if checksum != backup["manifest"]["checksum"]:
            raise ValueError("backup checksum mismatch")
        return cls([ServiceNode(**node) for node in json.loads(payload)])
