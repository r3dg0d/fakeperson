"""CPU stub backend — deterministic placeholder PNG for tests / no-CUDA boxes."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..metadata_png import stamp_synthetic


class StubBackend:
    name = "stub"

    def generate(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        seed: int,
        outfile: str,
        width: int = 768,
        height: int = 1024,
    ) -> str:
        # Deterministic color from seed
        digest = hashlib.sha256(f"{seed}:{prompt[:80]}".encode()).digest()
        bg = tuple(digest[i] for i in range(3))
        accent = tuple(digest[i + 3] for i in range(3))

        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)
        # Simple "face" silhouette so gallery isn't a flat color
        cx, cy = width // 2, height // 3
        r = min(width, height) // 5
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=accent)
        draw.rectangle(
            (cx - r // 2, cy + r, cx + r // 2, cy + r * 3),
            fill=tuple((c + 40) % 256 for c in accent),
        )
        label = f"SYNTHETIC\nfakeperson stub\nseed={seed}"
        try:
            font = ImageFont.load_default()
        except OSError:
            font = None
        draw.multiline_text((24, height - 120), label, fill=(255, 255, 255), font=font)

        path = Path(outfile)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")
        img.save(path)
        stamp_synthetic(path, prompt=prompt, seed=seed)
        _ = negative_prompt  # used by real backends
        return str(path)
