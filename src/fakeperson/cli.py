"""Click CLI for fakeperson."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .generate import generate_batch, render_identity
from .identity import create_identity, list_identities, load_identity
from .models import install_model, list_models
from .paths import ensure_dirs
from .prompt import PersonAttrs, STYLES


def _attrs_from_params(kwargs: dict) -> PersonAttrs:
    return PersonAttrs(
        age=kwargs.get("age"),
        hairstyle=kwargs.get("hairstyle"),
        facial_structure=kwargs.get("facial_structure"),
        expression=kwargs.get("expression"),
        clothing=kwargs.get("clothing"),
        pose=kwargs.get("pose"),
        background=kwargs.get("background"),
        lighting=kwargs.get("lighting"),
        camera=kwargs.get("camera"),
        lens=kwargs.get("lens"),
        dof=kwargs.get("dof"),
        skin_detail=kwargs.get("skin_detail"),
        imperfections=kwargs.get("imperfections"),
        grain=kwargs.get("grain"),
        aspect_ratio=kwargs.get("aspect_ratio"),
        style=kwargs.get("style") or "studio",
        extra_prompt=kwargs.get("prompt"),
    )


def person_options(fn):
    opts = [
        click.option("--age", default=None, help="Apparent age description"),
        click.option("--hairstyle", default=None),
        click.option("--facial-structure", default=None),
        click.option("--expression", default=None),
        click.option("--clothing", default=None),
        click.option("--pose", default=None),
        click.option("--background", default=None),
        click.option("--lighting", default=None),
        click.option("--camera", default=None, help="Camera body / framing hints"),
        click.option("--lens", default=None),
        click.option("--dof", default=None, help="Depth of field"),
        click.option("--skin-detail", default=None),
        click.option("--imperfections", default=None),
        click.option("--grain", default=None),
        click.option("--aspect-ratio", default="3:4", show_default=True),
        click.option(
            "--style",
            type=click.Choice(sorted(STYLES.keys())),
            default="studio",
            show_default=True,
        ),
        click.option("--prompt", default=None, help="Extra prompt text folded in"),
        click.option(
            "--backend",
            type=click.Choice(["auto", "text2img", "stub"]),
            default="auto",
            show_default=True,
        ),
    ]
    for opt in reversed(opts):
        fn = opt(fn)
    return fn


@click.group()
@click.version_option(__version__, prog_name="fakeperson")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Photorealistic fictional people — synthetic identities with optional text2img."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ensure_dirs()


@main.command("generate")
@click.option("--count", default=1, show_default=True, type=int)
@click.option("--seed", default=None, type=int)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("fakeperson-out"),
    show_default=True,
)
@person_options
@click.pass_context
def generate_cmd(ctx: click.Context, count: int, seed: int | None, output_dir: Path, **kwargs):
    """Generate one or more fictional people."""
    if count < 1 or count > 100:
        raise click.ClickException("--count must be 1..100")
    attrs = _attrs_from_params(kwargs)
    backend = kwargs.get("backend")
    if backend == "auto":
        backend = None
    try:
        results = generate_batch(
            attrs,
            count=count,
            seed=seed,
            out_dir=output_dir,
            backend_name=backend,
        )
    except Exception as e:  # noqa: BLE001 — CLI boundary
        raise click.ClickException(str(e)) from e

    for r in results:
        click.echo(f"{r['path']}  seed={r['seed']}  backend={r['backend']}")
        if ctx.obj.get("verbose"):
            click.echo(f"  prompt: {r['prompt'][:200]}...")
            if r["meta"].get("rewritten"):
                click.echo(f"  safeguard: {r['meta'].get('rewrite_reason')}")


@main.group("identity")
def identity_group():
    """Manage persistent synthetic identities."""


@identity_group.command("create")
@click.option("--name", required=True, help="Identity id (filesystem-safe)")
@click.option("--seed", default=None, type=int)
@click.option(
    "--style",
    type=click.Choice(sorted(STYLES.keys())),
    default="studio",
    show_default=True,
)
@click.option("--attr", multiple=True, help="key=value locked attribute (repeatable)")
@click.option("--notes", default="")
def identity_create(name: str, seed: int | None, style: str, attr: tuple[str, ...], notes: str):
    """Create a named identity (seed + locked traits)."""
    attributes: dict = {}
    for item in attr:
        if "=" not in item:
            raise click.ClickException(f"--attr must be key=value, got {item!r}")
        k, v = item.split("=", 1)
        attributes[k.strip()] = v.strip()
    try:
        ident = create_identity(
            name, seed=seed, style=style, attributes=attributes, notes=notes
        )
    except (ValueError, FileExistsError) as e:
        raise click.ClickException(str(e)) from e
    click.echo(f"created identity {ident.name} seed={ident.seed} style={ident.style_lock}")
    click.echo(f"stored under {ident.path()}")


@identity_group.command("list")
@click.option("--json", "as_json", is_flag=True)
def identity_list(as_json: bool):
    """List saved identities."""
    items = list_identities()
    if as_json:
        click.echo(json.dumps([i.to_dict() for i in items], indent=2))
        return
    if not items:
        click.echo("(no identities)")
        return
    for i in items:
        click.echo(f"{i.name}\tseed={i.seed}\tstyle={i.style_lock}")


@identity_group.command("render")
@click.argument("name")
@click.option("--prompt", default=None, help="Extra scene prompt while keeping locked face traits")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
)
@click.option(
    "--style",
    type=click.Choice(sorted(STYLES.keys())),
    default=None,
)
@click.option(
    "--backend",
    type=click.Choice(["auto", "text2img", "stub"]),
    default="auto",
)
def identity_render(
    name: str, prompt: str | None, output: Path | None, style: str | None, backend: str
):
    """Render a saved identity with optional extra prompt."""
    try:
        load_identity(name)
    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    out = output or Path(f"fakeperson-out/{name}.png")
    be = None if backend == "auto" else backend
    try:
        result = render_identity(
            name, extra_prompt=prompt, outfile=out, backend_name=be, style=style
        )
    except Exception as e:  # noqa: BLE001
        raise click.ClickException(str(e)) from e
    click.echo(f"{result['path']}  seed={result['seed']}  backend={result['backend']}")


@main.group("models")
def models_group():
    """List / install backends (never silent giant downloads)."""


@models_group.command("list")
@click.option("--json", "as_json", is_flag=True)
def models_list(as_json: bool):
    """Show catalog with license, size hints, install state."""
    rows = list_models()
    if as_json:
        click.echo(
            json.dumps(
                [
                    {
                        "name": r.name,
                        "installed": r.installed,
                        **r.meta,
                    }
                    for r in rows
                ],
                indent=2,
            )
        )
        return
    for r in rows:
        mark = "yes" if r.installed else "no"
        click.echo(f"{r.name}\tinstalled={mark}\tsize={r.meta.get('size_hint')}")
        click.echo(f"  source: {r.meta.get('source')}")
        click.echo(f"  license: {r.meta.get('license')}")
        if r.meta.get("notes"):
            click.echo(f"  notes: {r.meta['notes']}")


@models_group.command("install")
@click.argument("model")
@click.option("--yes", is_flag=True, help="Confirm downloads when a catalog entry requires them")
def models_install(model: str, yes: bool):
    """Explicitly install/verify a model backend."""
    try:
        msg = install_model(model, yes=yes)
    except (KeyError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e
    click.echo(msg)


if __name__ == "__main__":
    main(prog_name="fakeperson")
