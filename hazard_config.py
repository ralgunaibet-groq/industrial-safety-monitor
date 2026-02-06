"""
Shared hazard configuration loader and prompt builder.

Reads hazard_config.yaml to allow users to customize which hazard
categories are monitored and which keywords are used for incident
comparison.
"""

import os
import yaml
from pathlib import Path

_CONFIG_FILENAME = "hazard_config.yaml"
_cached_config = None


def _find_config_path():
    """Locate the hazard config file relative to this module."""
    return Path(__file__).parent / _CONFIG_FILENAME


def load_config(path=None):
    """Load and cache the hazard configuration from YAML.

    Parameters
    ----------
    path : str or Path, optional
        Override path to the config file.  When *None* the file is
        expected next to this module.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    config_path = Path(path) if path else _find_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Hazard config not found at {config_path}. "
            "Please create hazard_config.yaml (see README)."
        )

    with open(config_path, "r") as fh:
        _cached_config = yaml.safe_load(fh)

    return _cached_config


def reload_config(path=None):
    """Force-reload the configuration (clears cache)."""
    global _cached_config
    _cached_config = None
    return load_config(path)


def get_enabled_hazard_categories(config=None):
    """Return only the hazard categories that are enabled.

    Each item is a dict with *name*, *enabled*, and *description* keys.
    """
    if config is None:
        config = load_config()
    return [
        cat for cat in config.get("hazard_categories", [])
        if cat.get("enabled", True)
    ]


def build_hazard_prompt(config=None):
    """Build the hazard-detection prompt from the current configuration.

    The prompt preserves the original structure but injects the enabled
    hazard categories dynamically.
    """
    categories = get_enabled_hazard_categories(config)

    bullet_lines = "\n".join(
        f"  - {cat['name']}: {cat['description']}" for cat in categories
    )

    return f"""\
You are an industrial safety inspector looking at a live camera feed
from an industrial site (factory, plant, warehouse, refinery, construction, etc.).

Your job is to:
- Detect any visible safety hazards or dangerous situations.
- Focus on things like:
{bullet_lines}
- If nothing looks unsafe, say so clearly.

Respond ONLY as valid JSON with this exact structure:
{{
  "hazard_present": true or false,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "hazard_types": [list of short strings],
  "description": "one or two sentences describing the scene and any hazards",
  "recommended_actions": [list of short actionable recommendations]
}}

Do not include any text before or after the JSON."""


def get_incident_keywords(config=None):
    """Return the incident-comparison keyword lists from the config.

    Returns
    -------
    dict
        Keys are ``actors``, ``actions``, ``objects``, ``locations``
        each mapping to a list of strings.
    """
    if config is None:
        config = load_config()
    defaults = {
        "actors": [],
        "actions": [],
        "objects": [],
        "locations": [],
    }
    keywords = config.get("incident_keywords", {})
    for key in defaults:
        if key not in keywords:
            keywords[key] = defaults[key]
    return keywords
