"""Model catalog + explicit install (never silent giant downloads)."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import ensure_dirs, models_dir

# Catalog entries are metadata only. Large weights require explicit `models install`.
CATALOG: dict[str, dict[str, Any]] = {
    "text2img": {
        "name": "text2img",
        "backend": "text2img",
        "source": "local PATH binary (LLaDA-Image Turbo / text2img on Vincent's machine)",
        "license": "See text2img / LLaDA-Image upstream terms",
        "size_hint": "0 (wrapper) — model weights managed by text2img itself",
        "checksum": None,
        "install": "verify",
        "binaries": ["text2img", "llada-image"],
        "notes": "Preferred backend when available. models install only verifies PATH.",
    },
    "stub": {
        "name": "stub",
        "backend": "stub",
        "source": "built-in placeholder renderer (no network)",
        "license": "MIT (fakeperson)",
        "size_hint": "0",
        "checksum": None,
        "install": "local",
        "notes": "Used on CUDA-less boxes for CLI/tests; produces marked synthetic PNGs.",
    },
}


@dataclass
class ModelInfo:
    name: str
    installed: bool
    meta: dict[str, Any]
    path: Path | None = None


def list_models() -> list[ModelInfo]:
    ensure_dirs()
    installed_marker = models_dir() / "installed.json"
    installed: dict[str, Any] = {}
    if installed_marker.is_file():
        try:
            installed = json.loads(installed_marker.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            installed = {}

    out: list[ModelInfo] = []
    for name, meta in CATALOG.items():
        path = models_dir() / name
        is_in = name in installed or (path.is_dir() and any(path.iterdir()))
        if name == "text2img":
            is_in = is_in or any(shutil.which(b) for b in meta.get("binaries", []))
        if name == "stub":
            is_in = True
        out.append(ModelInfo(name=name, installed=bool(is_in), meta=meta, path=path if path.exists() else None))
    return out


def _mark_installed(name: str, extra: dict[str, Any] | None = None) -> None:
    ensure_dirs()
    marker = models_dir() / "installed.json"
    data: dict[str, Any] = {}
    if marker.is_file():
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    entry = {"name": name, **(extra or {})}
    data[name] = entry
    marker.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install_model(name: str, *, yes: bool = False) -> str:
    """Explicit install. Never downloads large weights without confirmation semantics."""
    if name not in CATALOG:
        known = ", ".join(sorted(CATALOG))
        raise KeyError(f"unknown model '{name}'. Known: {known}")

    meta = CATALOG[name]
    ensure_dirs()
    target = models_dir() / name
    target.mkdir(parents=True, exist_ok=True)

    if meta["install"] == "verify":
        bins = meta.get("binaries") or []
        found = {b: shutil.which(b) for b in bins}
        if not any(found.values()):
            raise RuntimeError(
                f"model '{name}' requires one of {bins} on PATH. "
                "No silent download — install the upstream tool first, then re-run "
                f"`fakeperson models install {name}`."
            )
        (target / "BACKEND.txt").write_text(
            "text2img backend — weights are owned by the external binary.\n"
            + json.dumps(found, indent=2)
            + "\n",
            encoding="utf-8",
        )
        _mark_installed(name, {"verified_bins": found})
        return f"Verified text2img backend: { {k:v for k,v in found.items() if v} }"

    if meta["install"] == "local":
        (target / "STUB.txt").write_text(
            "Built-in stub backend — no weights.\n", encoding="utf-8"
        )
        _mark_installed(name, {"stub": True})
        return f"Stub backend ready at {target}"

    # Future: real downloads would require --yes and checksum verification here.
    if not yes:
        raise RuntimeError(
            f"Refusing to download model '{name}' without explicit confirmation. "
            "Re-run with --yes after reviewing license/size in `models list`. "
            "fakeperson never silently downloads large weights."
        )
    raise RuntimeError(f"Download installer for '{name}' is not wired in this version.")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
