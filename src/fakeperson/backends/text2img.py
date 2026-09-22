"""Adapter for local `text2img` / `llada-image` (LLaDA-Image Turbo) CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..metadata_png import stamp_synthetic


class Text2ImgBackend:
    name = "text2img"

    def __init__(self) -> None:
        self.bin = shutil.which("text2img") or shutil.which("llada-image")
        if not self.bin:
            raise RuntimeError("text2img/llada-image not found on PATH")

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

        # Best-effort CLI shapes — try common flag styles; document failures clearly.
        attempts = [
            [
                self.bin,
                "--prompt",
                prompt,
                "--negative-prompt",
                negative_prompt,
                "--seed",
                str(seed),
                "--width",
                str(width),
                "--height",
                str(height),
                "--output",
                str(path),
            ],
            [
                self.bin,
                "-p",
                prompt,
                "-n",
                negative_prompt,
                "-s",
                str(seed),
                "-o",
                str(path),
            ],
            [self.bin, prompt, "--seed", str(seed), "-o", str(path)],
        ]

        last_err = None
        for cmd in attempts:
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=600,
                )
            except subprocess.TimeoutExpired as e:
                last_err = e
                continue
            if proc.returncode == 0 and path.exists():
                stamp_synthetic(path, prompt=prompt, seed=seed)
                return str(path)
            last_err = RuntimeError(
                f"exit {proc.returncode}: {(proc.stderr or proc.stdout or '')[:500]}"
            )

        raise RuntimeError(
            f"text2img backend failed to produce {path}. Last error: {last_err}. "
            "On machines without CUDA, use --backend stub."
        )
