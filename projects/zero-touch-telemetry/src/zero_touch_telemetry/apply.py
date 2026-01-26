"""Apply Zero-Touch Telemetry plans to a cluster."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def apply_plan_dict(
    plan: Dict[str, Any],
    kubectl: str = "kubectl",
    dry_run: bool = False,
    output_dir: Optional[Path] = None,
) -> List[str]:
    commands: List[str] = []
    manifest_yaml = plan.get("collector", {}).get("manifest_yaml")
    patches = plan.get("collector", {}).get("patches", [])

    manifest_path = None
    if manifest_yaml:
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = output_dir / "collector-manifest.yaml"
            manifest_path.write_text(manifest_yaml, encoding="utf-8")
        else:
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
            manifest_path = Path(handle.name)
            handle.write(manifest_yaml.encode("utf-8"))
            handle.close()
        commands.append(f"{kubectl} apply -f {manifest_path}")
        if not dry_run:
            _run([kubectl, "apply", "-f", str(manifest_path)])

    for patch in patches:
        kind = str(patch.get("kind", "deployment")).lower()
        name = patch.get("workload_name")
        namespace = patch.get("namespace", "default")
        payload = json.dumps(patch.get("patch", {}))
        cmd = [kubectl, "patch", kind, name, "-n", namespace, "--type", "merge", "-p", payload]
        commands.append(" ".join(cmd))
        if not dry_run:
            _run(cmd)

    return commands


def _run(cmd: Iterable[str]) -> None:
    subprocess.run(list(cmd), check=True)
