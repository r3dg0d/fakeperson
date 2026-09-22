"""Persistent synthetic identities (seed + locked attributes)."""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import ensure_dirs, identities_dir
from .safeguards import identity_name_ok


@dataclass
class Identity:
    name: str
    seed: int
    style_lock: str = "studio"
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""

    def path(self) -> Path:
        return identities_dir() / self.name / "identity.json"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Identity:
        return cls(
            name=data["name"],
            seed=int(data["seed"]),
            style_lock=data.get("style_lock", "studio"),
            attributes=dict(data.get("attributes") or {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            notes=data.get("notes", ""),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_identity(
    name: str,
    *,
    seed: int | None = None,
    style: str = "studio",
    attributes: dict[str, Any] | None = None,
    notes: str = "",
) -> Identity:
    check = identity_name_ok(name)
    if not check.allowed:
        raise ValueError(check.reason or "invalid identity name")

    ensure_dirs()
    dest = identities_dir() / name
    if dest.exists():
        raise FileExistsError(f"identity already exists: {name}")

    ident = Identity(
        name=name,
        seed=seed if seed is not None else secrets.randbits(31),
        style_lock=style,
        attributes=attributes or {},
        created_at=_now(),
        updated_at=_now(),
        notes=notes,
    )
    dest.mkdir(parents=True, exist_ok=True)
    ident.path().write_text(json.dumps(ident.to_dict(), indent=2) + "\n", encoding="utf-8")
    return ident


def load_identity(name: str) -> Identity:
    path = identities_dir() / name / "identity.json"
    if not path.is_file():
        raise FileNotFoundError(f"identity not found: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Identity.from_dict(data)


def save_identity(ident: Identity) -> None:
    ident.updated_at = _now()
    ensure_dirs()
    dest = identities_dir() / ident.name
    dest.mkdir(parents=True, exist_ok=True)
    ident.path().write_text(json.dumps(ident.to_dict(), indent=2) + "\n", encoding="utf-8")


def list_identities() -> list[Identity]:
    ensure_dirs()
    root = identities_dir()
    out: list[Identity] = []
    if not root.is_dir():
        return out
    for child in sorted(root.iterdir()):
        meta = child / "identity.json"
        if meta.is_file():
            try:
                out.append(Identity.from_dict(json.loads(meta.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
    return out
