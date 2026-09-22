"""Adapter for local `text2img` (LLaDA-Image Turbo) CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..metadata_png import stamp_synthetic


class Text2ImgBackend:
    name = "text2img"

    def __init__(self) -> None:
        # Prefer text2img (generation) over llada-image (service control).
        self.bin = shutil.which("text2img")
        if not self.bin:
            raise RuntimeError("text2img not found on PATH")

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
        path = Path(outfile)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Match zionsec llada-cli text2img flags exactly (see `text2img --help`).
        cmd = [
            self.bin,
            "--prompt",
            prompt,
            "--negative-prompt",
            negative_prompt or "blurry, low detail, deformed, celebrity likeness",
            "--seed",
            str(seed),
            "--width",
            str(width),
            "--height",
            str(height),
            "--output",
            str(path.resolve()),
            "--keep-alive",
            "600",
            "--device",
            "cuda",
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )
        if proc.returncode != 0 or not path.exists():
            raise RuntimeError(
                "text2img backend failed to produce "
                f"{path}. exit={proc.returncode} stderr={(proc.stderr or '')[:800]} "
                f"stdout={(proc.stdout or '')[:400]}. "
                "On machines without CUDA, use --backend stub."
            )
        stamp_synthetic(path, prompt=prompt, seed=seed)
        return str(path)
