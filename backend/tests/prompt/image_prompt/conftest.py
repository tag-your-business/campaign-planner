"""Session fixture: generate campaign_specs.json from profile variants + CampaignPlanner."""

import json
import os
from pathlib import Path

import pytest
import yaml
from app.features.generation.planner import CampaignPlanner


def _build_context(spec: dict) -> list[str]:
    brand_colors = spec.get("brand_colors", {})
    if brand_colors:
        primary = brand_colors.get("primary", "")
        accent = brand_colors.get("accent", "")
        colors_label = ", ".join(filter(None, [primary, accent]))
    else:
        colors_label = "none (natural vibrant tones)"
    tone_text = ", ".join(spec.get("tone_keywords", []))
    return [
        f"Event: {spec.get('event_name')}",
        f"Company: {spec.get('company_name')} — {spec.get('industry')}",
        f"Tone: {tone_text}",
        f"Visual style: {spec.get('visual_style')}",
        f"Brand colors: {colors_label}",
    ]


@pytest.fixture(scope="session", autouse=True)
def generate_campaign_specs() -> None:
    if os.environ.get("RUN_LLM_EVAL") != "1":
        return

    feature_dir = Path(__file__).parent
    backend_dir = feature_dir.parents[2]

    with open(feature_dir / "config.yaml") as f:
        config = yaml.safe_load(f)

    gen_cfg = config.get("campaign_spec_generation", {})
    profiles_dir = feature_dir / gen_cfg["profiles_dir"]
    event_file = backend_dir / gen_cfg["event_file"]
    event_id = gen_cfg["event_id"]
    profile_names: list[str] = gen_cfg["profiles"]

    with open(event_file) as f:
        events: list[dict] = json.load(f)

    event = next((e for e in events if e["id"] == event_id), None)
    if event is None:
        raise ValueError(f"Event '{event_id}' not found in {event_file}")

    planner = CampaignPlanner()
    specs: list[dict] = []

    for profile_name in profile_names:
        with open(profiles_dir / f"{profile_name}.json") as f:
            profile: dict = json.load(f)

        spec = planner.plan(profile, event)
        if spec is None:
            raise ValueError(
                f"CampaignPlanner returned None for '{profile_name}' + event '{event_id}'"
            )

        spec["model_branding"] = profile.get("model_branding", False)
        if spec["model_branding"]:
            spec["contact_info"] = profile.get("contact_info", {})
        spec["profile_version"] = profile_name

        tone_label = ", ".join(spec.get("tone_keywords", []))
        brand_colors = spec.get("brand_colors", {})
        if brand_colors:
            primary = brand_colors.get("primary", "")
            accent = brand_colors.get("accent", "")
            colors_suffix = f"({primary} + {accent} palette)"
        else:
            colors_suffix = "(no brand colors)"

        spec["input_description"] = (
            f"Diwali campaign for {spec['company_name']}"
            f" [{profile_name}] — {tone_label} {colors_suffix}"
        )
        spec["context"] = _build_context(spec)
        specs.append(spec)

    output_path = feature_dir / "data" / "campaign_specs.json"
    with open(output_path, "w") as f:
        json.dump(specs, f, indent=2)
