"""Prompt + negative-prompt builder for photorealistic fictional people."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .safeguards import CELEBRITY_NEGATIVES, scrub_public_figure

STYLES = {
    "selfie": {
        "camera": "smartphone front camera, slight wide angle, arm's length",
        "lighting": "natural window light, soft fill",
        "pose": "casual selfie pose, looking into lens",
        "background": "everyday indoor background, softly blurred",
    },
    "studio": {
        "camera": "85mm portrait lens on full-frame camera",
        "lighting": "softbox key light, gentle rim light, controlled studio",
        "pose": "professional head-and-shoulders pose",
        "background": "seamless neutral studio backdrop",
    },
    "passport": {
        "camera": "50mm equivalent, eye-level, neutral perspective",
        "lighting": "even frontal lighting, no dramatic shadows",
        "pose": "neutral expression, facing camera, shoulders square",
        "background": "plain light-gray or white backdrop",
    },
    "candid": {
        "camera": "35mm street photography, natural framing",
        "lighting": "available light, realistic contrast",
        "pose": "candid mid-action, not posing for camera",
        "background": "real-world environment, shallow depth of field",
    },
}


@dataclass
class PersonAttrs:
    age: str | None = None
    hairstyle: str | None = None
    facial_structure: str | None = None
    expression: str | None = None
    clothing: str | None = None
    pose: str | None = None
    background: str | None = None
    lighting: str | None = None
    camera: str | None = None
    lens: str | None = None
    dof: str | None = None
    skin_detail: str | None = None
    imperfections: str | None = None
    grain: str | None = None
    aspect_ratio: str | None = None
    style: str = "studio"
    extra_prompt: str | None = None
    locked: dict[str, Any] = field(default_factory=dict)

    def merged(self) -> dict[str, str]:
        """Style defaults < locked identity traits < explicit attrs."""
        base = dict(STYLES.get(self.style, STYLES["studio"]))
        out: dict[str, str] = {k: v for k, v in base.items()}
        for k, v in self.locked.items():
            if v:
                out[k] = str(v)
        mapping = {
            "age": self.age,
            "hairstyle": self.hairstyle,
            "facial_structure": self.facial_structure,
            "expression": self.expression,
            "clothing": self.clothing,
            "pose": self.pose,
            "background": self.background,
            "lighting": self.lighting,
            "camera": self.camera,
            "lens": self.lens,
            "dof": self.dof,
            "skin_detail": self.skin_detail,
            "imperfections": self.imperfections,
            "grain": self.grain,
            "aspect_ratio": self.aspect_ratio,
        }
        for k, v in mapping.items():
            if v:
                out[k] = v
        if self.lens and "camera" in out and self.lens not in out["camera"]:
            out["camera"] = f"{out['camera']}, {self.lens}"
        return out


def build_prompts(
    attrs: PersonAttrs,
    *,
    identity_name: str | None = None,
    seed: int | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Return (prompt, negative_prompt, meta)."""
    parts: list[str] = [
        "photorealistic photograph of a completely fictional adult person",
        "original face, unique individual, not based on any real person",
    ]
    if identity_name:
        parts.append(f"consistent character identity '{identity_name}'")
    if seed is not None:
        parts.append(f"identity seed {seed}")

    merged = attrs.merged()
    order = [
        "age",
        "facial_structure",
        "hairstyle",
        "expression",
        "clothing",
        "pose",
        "background",
        "lighting",
        "camera",
        "dof",
        "skin_detail",
        "imperfections",
        "grain",
        "aspect_ratio",
    ]
    for key in order:
        if key in merged and merged[key]:
            label = key.replace("_", " ")
            parts.append(f"{label}: {merged[key]}")

    if attrs.extra_prompt:
        parts.append(attrs.extra_prompt)

    raw = ", ".join(parts)
    sg = scrub_public_figure(raw, allow_rewrite=True)
    prompt = sg.prompt

    negatives = [
        CELEBRITY_NEGATIVES,
        "deformed face, extra fingers, watermark, logo, text overlay, lowres, cartoon, anime",
        "child, underage, minor",
    ]
    negative = ", ".join(negatives)

    meta = {
        "style": attrs.style,
        "rewritten": sg.rewritten,
        "rewrite_reason": sg.reason,
        "merged_attrs": merged,
        "seed": seed,
        "identity_name": identity_name,
    }
    return prompt, negative, meta
