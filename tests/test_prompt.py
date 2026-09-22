from fakeperson.prompt import PersonAttrs, build_prompts, STYLES


def test_styles_exist():
    assert set(STYLES) >= {"selfie", "studio", "passport", "candid"}


def test_build_includes_attrs_and_negatives():
    attrs = PersonAttrs(
        style="studio",
        age="early 30s",
        hairstyle="short wavy brown hair",
        expression="slight smile",
    )
    prompt, neg, meta = build_prompts(attrs, seed=42)
    assert "fictional" in prompt.lower()
    assert "early 30s" in prompt
    assert "short wavy brown hair" in prompt
    assert "celebrity likeness" in neg
    assert meta["seed"] == 42
    assert meta["style"] == "studio"


def test_locked_traits_override_style_defaults():
    attrs = PersonAttrs(
        style="selfie",
        locked={"hairstyle": "locked bob cut", "age": "40s"},
        hairstyle="should be overridden? no — explicit wins",
    )
    # explicit attr should win over locked
    prompt, _, meta = build_prompts(attrs)
    assert "should be overridden" in prompt
    assert meta["merged_attrs"]["age"] == "40s"
