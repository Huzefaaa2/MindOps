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
    diff: bool = False,
    diff_only: bool = False,
    output_dir: Optional[Path] = None,
) -> List[str]:
    commands: List[str] = []
    manifest_yaml = plan.get("collector", {}).get("manifest_yaml")
    patches = plan.get("collector", {}).get("patches", [])

    manifest_path = None
    if diff_only:
        diff = True

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
        if diff:
            commands.append(f"{kubectl} diff -f {manifest_path}")
            if not dry_run:
                _run([kubectl, "diff", "-f", str(manifest_path)])
        if not diff_only:
            commands.append(f"{kubectl} apply -f {manifest_path}")
            if not dry_run:
                _run([kubectl, "apply", "-f", str(manifest_path)])

    for patch in patches:
        kind = str(patch.get("kind", "deployment")).lower()
        name = patch.get("workload_name")
        namespace = patch.get("namespace", "default")
        payload = json.dumps(patch.get("patch", {}))
        cmd = [kubectl, "patch", kind, name, "-n", namespace, "--type", "merge", "-p", payload]
        if diff:
            diff_cmd = [kubectl, "diff", "-n", namespace, "-f", "-"]
            commands.append(" ".join(diff_cmd))
            if not dry_run:
                diff_payload = json.dumps({
                    "apiVersion": "apps/v1",
                    "kind": patch.get("kind", "Deployment"),
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": patch.get("patch", {}).get("spec", {}),
                })
                _run_stdin(diff_cmd, diff_payload)
        if not diff_only:
            commands.append(" ".join(cmd))
            if not dry_run:
                _run(cmd)

    return commands


def _run(cmd: Iterable[str]) -> None:
    subprocess.run(list(cmd), check=True)


def _run_stdin(cmd: Iterable[str], payload: str) -> None:
    subprocess.run(list(cmd), input=payload.encode("utf-8"), check=True)
