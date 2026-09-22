# fakeperson

Modern CLI for **photorealistic fictional people**. Creates consistent *synthetic identities* (seed + locked facial/style traits) and renders them via a pluggable model backend.

## Research & consent framing

This tool is for **clearly synthetic, fictional** adults — privacy demos, UX mockups, red-team scenarios that must not depict real people, and creative work.

- **Do not** request likenesses of real public figures, private individuals, or minors.
- Safeguards rewrite/refuse likely celebrity prompts and always add negative prompts against celebrity likeness.
- Output PNGs are stamped with `Software=fakeperson` and `Disclaimer=synthetic`.
- Generating a face does **not** grant rights to impersonate anyone, commit fraud, or harass.

If your use case involves consent-sensitive media (journalism, evidence, political content), prefer non-photoreal avatars or fully disclosed composites — and follow local law.

## Backends

| Backend | When | Notes |
|---------|------|--------|
| **text2img** | `text2img` or `llada-image` on `PATH` (e.g. LLaDA-Image Turbo on Vincent’s CUDA machine) | Preferred. `models install text2img` **only verifies PATH** — never downloads giant weights silently. |
| **stub** | Default fallback / CI / this Debian box without CUDA | Deterministic placeholder PNG with synthetic metadata. |

## Install

```bash
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
fakeperson --help
```

Nix: `nix develop` via `flake.nix` (provides Python + deps when Nix is available).

## Usage

```bash
# One-off people
fakeperson generate
fakeperson generate --count 10
fakeperson generate --seed 12345 --style selfie
fakeperson generate --style studio --age "late 20s" --hairstyle "short black hair" \
  --facial-structure "oval face, high cheekbones" --expression "neutral" \
  --clothing "linen shirt" --aspect-ratio 3:4 --backend stub

# Persistent identity (same person across scenes)
fakeperson identity create --name alice --seed 12345 --style passport \
  --attr "hairstyle=wavy auburn" --attr "age=32" --attr "facial_structure=soft jaw"
fakeperson identity render alice --prompt "standing in a rainy neon street, candid"
fakeperson identity list

# Models (explicit install only)
fakeperson models list
fakeperson models install text2img   # verifies binary on PATH
fakeperson models install stub
```

Attribute flags fold into the positive prompt; celebrity negatives are always attached.

Data dirs:

- Identities: `~/.local/share/fakeperson/identities/<name>/identity.json`
- Model cache markers: `~/.cache/fakeperson/models/`

## Gallery

Placeholder gallery (stub renders). On CUDA hosts with `text2img`, replace these with real samples:

| Style | Placeholder |
|-------|-------------|
| studio | `gallery/placeholder_studio.png` |
| selfie | `gallery/placeholder_selfie.png` |
| passport | `gallery/placeholder_passport.png` |
| candid | `gallery/placeholder_candid.png` |

Generate placeholders:

```bash
fakeperson generate --backend stub --style studio --seed 1 -o gallery --count 1
# rename/move as needed into gallery/placeholder_*.png
```

## License

MIT — see [LICENSE](LICENSE).
