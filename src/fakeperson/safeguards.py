"""Refuse / rewrite prompts that look like public-figure likeness requests."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Small denylist of high-profile names / roles. Not exhaustive — heuristic only.
_PUBLIC_FIGURE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.I)
    for p in [
        r"\b(taylor\s+swift|beyonc[eé]|rihanna|drake|kanye|kim\s+kardashian)\b",
        r"\b(elon\s+musk|donald\s+trump|joe\s+biden|barack\s+obama|kamala\s+harris)\b",
        r"\b(tom\s+cruise|brad\s+pitt|angelina\s+jolie|scarlett\s+johansson)\b",
        r"\b(keanu\s+reeves|leonardo\s+dicaprio|meryl\s+streep|denzel\s+washington)\b",
        r"\b(oprah|zelenskyy|putin|xi\s+jinping|king\s+charles)\b",
        r"\b(celebrity\s+likeness|famous\s+actor|lookalike\s+of|looks?\s+like\s+[A-Z][a-z]+\s+[A-Z][a-z]+)\b",
        r"\bas\s+(president|prime\s+minister|pope)\s+[A-Z]",
    ]
]

CELEBRITY_NEGATIVES = (
    "celebrity likeness, famous person, known actor face, politician face, "
    "identifiable public figure, lookalike of a real celebrity"
)


@dataclass
class SafeguardResult:
    allowed: bool
    prompt: str
    reason: str | None = None
    rewritten: bool = False


def scrub_public_figure(prompt: str, *, allow_rewrite: bool = True) -> SafeguardResult:
    """Return whether generation should proceed, optionally rewriting the prompt."""
    text = prompt.strip()
    for pat in _PUBLIC_FIGURE_PATTERNS:
        if pat.search(text):
            if not allow_rewrite:
                return SafeguardResult(
                    allowed=False,
                    prompt=text,
                    reason="Prompt appears to request a public-figure / celebrity likeness.",
                )
            # Rewrite: strip the matching span and emphasize fictional identity.
            cleaned = pat.sub("a fictional anonymous person", text)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if not cleaned:
                cleaned = (
                    "photorealistic portrait of a completely fictional anonymous adult person"
                )
            return SafeguardResult(
                allowed=True,
                prompt=cleaned,
                reason="Public-figure-like phrasing was rewritten to a fictional person.",
                rewritten=True,
            )
    return SafeguardResult(allowed=True, prompt=text)


def identity_name_ok(name: str) -> SafeguardResult:
    """Block storing identities under obvious celebrity names."""
    probe = f"portrait of {name}"
    result = scrub_public_figure(probe, allow_rewrite=False)
    if not result.allowed:
        return SafeguardResult(
            allowed=False,
            prompt=name,
            reason=f"Identity name '{name}' looks like a public figure; choose a fictional name.",
        )
    # Also block empty / pathy names
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", name):
        return SafeguardResult(
            allowed=False,
            prompt=name,
            reason="Identity name must be 1–64 chars: letters, digits, _ or -.",
        )
    return SafeguardResult(allowed=True, prompt=name)
