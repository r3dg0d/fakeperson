"""High-level generate / identity-render orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .backends import select_backend
from .identity import Identity, load_identity
from .prompt import PersonAttrs, build_prompts


def aspect_to_size(aspect: str | None, default=(768, 1024)) -> tuple[int, int]:
    if not aspect:
        return default
    a = aspect.strip().lower().replace(" ", "")
    table = {
        "1:1": (1024, 1024),
        "3:4": (768, 1024),
        "4:3": (1024, 768),
        "9:16": (720, 1280),
        "16:9": (1280, 720),
        "2:3": (768, 1152),
        "3:2": (1152, 768),
    }
    if a in table:
        return table[a]
    if "x" in a:
        w, h = a.split("x", 1)
        return int(w), int(h)
    return default


def generate_one(
    attrs: PersonAttrs,
    *,
    seed: int,
    outfile: Path,
    backend_name: str | None = None,
    identity: Identity | None = None,
    prefer_identity_seed: bool = True,
) -> dict[str, Any]:
    if identity is not None:
        if not attrs.style:
            attrs.style = identity.style_lock
        # Locked traits win for recognizability across renders
        merged_locked = dict(identity.attributes)
        merged_locked.update(attrs.locked)
        attrs.locked = merged_locked
        if prefer_identity_seed:
            seed = identity.seed
        name = identity.name
    else:
        name = None

    prompt, negative, meta = build_prompts(attrs, identity_name=name, seed=seed)
    width, height = aspect_to_size(attrs.aspect_ratio)
    backend = select_backend(backend_name)
    path = backend.generate(
        prompt=prompt,
        negative_prompt=negative,
        seed=seed,
        outfile=str(outfile),
        width=width,
        height=height,
    )
    return {
        "path": path,
        "prompt": prompt,
        "negative_prompt": negative,
        "seed": seed,
        "backend": backend.name,
        "meta": meta,
    }


def generate_batch(
    attrs: PersonAttrs,
    *,
    count: int,
    seed: int | None,
    out_dir: Path,
    backend_name: str | None = None,
) -> list[dict[str, Any]]:
    import secrets

    out_dir.mkdir(parents=True, exist_ok=True)
    base_seed = seed if seed is not None else secrets.randbits(31)
    results = []
    for i in range(count):
        s = base_seed + i
        outfile = out_dir / f"person_{s}.png"
        results.append(
            generate_one(
                attrs,
                seed=s,
                outfile=outfile,
                backend_name=backend_name,
            )
        )
    return results


def render_identity(
    name: str,
    *,
    extra_prompt: str | None,
    outfile: Path,
    backend_name: str | None = None,
    style: str | None = None,
) -> dict[str, Any]:
    ident = load_identity(name)
    attrs = PersonAttrs(
        style=style or ident.style_lock,
        extra_prompt=extra_prompt,
        locked=dict(ident.attributes),
    )
    return generate_one(
        attrs,
        seed=ident.seed,
        outfile=outfile,
        backend_name=backend_name,
        identity=ident,
    )
