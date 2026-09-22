"""Image generation backends."""

from __future__ import annotations

import shutil
from typing import Protocol

from .stub import StubBackend
from .text2img import Text2ImgBackend


class Backend(Protocol):
    name: str

    def generate(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        seed: int,
        outfile: str,
        width: int,
        height: int,
    ) -> str: ...


def select_backend(preferred: str | None = None) -> Backend:
    if preferred == "stub":
        return StubBackend()
    if preferred in (None, "text2img", "auto"):
        if shutil.which("text2img") or shutil.which("llada-image"):
            return Text2ImgBackend()
        if preferred == "text2img":
            raise RuntimeError(
                "text2img/llada-image not on PATH. "
                "Run `fakeperson models install text2img` after installing the binary, "
                "or use --backend stub."
            )
    return StubBackend()
