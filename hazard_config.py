"""
Hazard Configuration Module

Loads and validates hazard category configuration from config.yaml.
Provides dynamic prompt generation based on enabled hazards.
"""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


class HazardConfigError(Exception):
    """Raised when hazard configuration is invalid."""
    pass


DEFAULT_HAZARD_CATEGORIES = [
    {
        "id": "missing_ppe",
        "name": "Missing PPE",
        "description": "No PPE (no helmet, no safety vest, no goggles, no gloves)",
        "enabled": True,
    },
    {
        "id": "machinery_proximity",
        "name": "Machinery Proximity",
        "description": "People too close to moving machinery or vehicles (forklifts, trucks, cranes)",
        "enabled": True,
    },
    {
        "id": "fall_hazard",
        "name": "Fall Hazard",
        "description": "Working at height without fall protection",
        "enabled": True,
    },
    {
        "id": "trip_hazard",
        "name": "Trip and Fall Hazard",
        "description": "Trip and fall hazards (cables, clutter, obstacles on floor)",
        "enabled": True,
    },
    {
        "id": "fire_hazard",
        "name": "Fire and Chemical Hazard",
        "description": "Fire, smoke, sparks, exposed hot surfaces, spills or leaks",
        "enabled": True,
    },
    {
        "id": "restricted_zone",
        "name": "Restricted Zone Violation",
        "description": "People in restricted zones or near dangerous equipment",
        "enabled": True,
    },
    {
        "id": "blocked_exit",
        "name": "Blocked Emergency Exit",
        "description": "Blocked emergency exits or escape routes",
        "enabled": True,
    },
]


def _validate_hazard_category(category: dict[str, Any], index: int) -> list[str]:
    """Validate a single hazard category entry. Returns list of error messages."""
    errors = []
    
    if not isinstance(category, dict):
        errors.append(f"Hazard category at index {index} must be a dictionary, got {type(category).__name__}")
        return errors
    
    required_fields = ["id", "name", "description"]
    for field in required_fields:
        if field not in category:
            errors.append(f"Hazard category at index {index} is missing required field '{field}'")
        elif not isinstance(category[field], str):
            errors.append(f"Hazard category at index {index}: '{field}' must be a string, got {type(category[field]).__name__}")
        elif not category[field].strip():
            errors.append(f"Hazard category at index {index}: '{field}' cannot be empty")
    
    if "enabled" in category and not isinstance(category["enabled"], bool):
        errors.append(f"Hazard category at index {index}: 'enabled' must be a boolean, got {type(category['enabled']).__name__}")
    
    return errors


def _validate_config(config: dict[str, Any]) -> list[str]:
    """Validate the entire configuration. Returns list of error messages."""
    errors = []
    
    if not isinstance(config, dict):
        errors.append(f"Configuration must be a dictionary, got {type(config).__name__}")
        return errors
    
    if "hazard_categories" not in config:
        errors.append("Configuration is missing required key 'hazard_categories'")
        return errors
    
    categories = config["hazard_categories"]
    if not isinstance(categories, list):
        errors.append(f"'hazard_categories' must be a list, got {type(categories).__name__}")
        return errors
    
    if len(categories) == 0:
        errors.append("'hazard_categories' cannot be empty - at least one hazard category is required")
        return errors
    
    seen_ids = set()
    for i, category in enumerate(categories):
        category_errors = _validate_hazard_category(category, i)
        errors.extend(category_errors)
        
        if isinstance(category, dict) and "id" in category:
            cat_id = category["id"]
            if cat_id in seen_ids:
                errors.append(f"Duplicate hazard category id '{cat_id}' at index {i}")
            seen_ids.add(cat_id)
    
    if not errors:
        enabled_count = sum(1 for c in categories if c.get("enabled", True))
        if enabled_count == 0:
            errors.append("At least one hazard category must be enabled")
    
    return errors


def load_hazard_config(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    """
    Load hazard categories from configuration file.
    
    Args:
        config_path: Path to config.yaml. If None, looks for config.yaml in the
                     same directory as this module, then falls back to defaults.
    
    Returns:
        List of hazard category dictionaries with keys: id, name, description, enabled
    
    Raises:
        HazardConfigError: If configuration is invalid
    """
    if config_path is None:
        module_dir = Path(__file__).parent
        config_path = module_dir / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"[CONFIG] No config file found at {config_path}, using default hazard categories")
        return DEFAULT_HAZARD_CATEGORIES.copy()
    
    if yaml is None:
        print("[CONFIG] PyYAML not installed, using default hazard categories")
        return DEFAULT_HAZARD_CATEGORIES.copy()
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise HazardConfigError(f"Failed to parse config file {config_path}: {e}")
    except OSError as e:
        raise HazardConfigError(f"Failed to read config file {config_path}: {e}")
    
    if config is None:
        raise HazardConfigError(f"Config file {config_path} is empty")
    
    errors = _validate_config(config)
    if errors:
        error_msg = f"Invalid configuration in {config_path}:\n" + "\n".join(f"  - {e}" for e in errors)
        raise HazardConfigError(error_msg)
    
    categories = []
    for category in config["hazard_categories"]:
        categories.append({
            "id": category["id"].strip(),
            "name": category["name"].strip(),
            "description": category["description"].strip(),
            "enabled": category.get("enabled", True),
        })
    
    enabled_count = sum(1 for c in categories if c["enabled"])
    print(f"[CONFIG] Loaded {len(categories)} hazard categories ({enabled_count} enabled) from {config_path}")
    
    return categories


def get_enabled_hazards(categories: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """
    Get only the enabled hazard categories.
    
    Args:
        categories: List of hazard categories. If None, loads from config file.
    
    Returns:
        List of enabled hazard category dictionaries
    """
    if categories is None:
        categories = load_hazard_config()
    return [c for c in categories if c.get("enabled", True)]


def build_hazard_prompt(categories: list[dict[str, Any]] | None = None) -> str:
    """
    Build the hazard detection prompt based on enabled hazard categories.
    
    Args:
        categories: List of hazard categories. If None, loads from config file.
    
    Returns:
        The complete hazard detection prompt string
    """
    enabled = get_enabled_hazards(categories)
    
    if not enabled:
        raise HazardConfigError("Cannot build prompt: no hazard categories are enabled")
    
    hazard_list = "\n".join(f"  - {h['description']}" for h in enabled)
    
    prompt = f"""
You are an industrial safety inspector looking at a live camera feed
from an industrial site (factory, plant, warehouse, refinery, construction, etc.).

Your job is to:
- Detect any visible safety hazards or dangerous situations.
- Focus on things like:
{hazard_list}
- If nothing looks unsafe, say so clearly.

Respond ONLY as valid JSON with this exact structure:
{{
  "hazard_present": true or false,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "hazard_types": [list of short strings],
  "description": "one or two sentences describing the scene and any hazards",
  "recommended_actions": [list of short actionable recommendations]
}}

Do not include any text before or after the JSON.
"""
    return prompt


_cached_prompt: str | None = None
_cached_categories: list[dict[str, Any]] | None = None


def get_hazard_prompt() -> str:
    """
    Get the hazard detection prompt, loading config if needed.
    Caches the result for performance.
    
    Returns:
        The complete hazard detection prompt string
    """
    global _cached_prompt, _cached_categories
    
    if _cached_prompt is None:
        _cached_categories = load_hazard_config()
        _cached_prompt = build_hazard_prompt(_cached_categories)
    
    return _cached_prompt


def get_hazard_categories() -> list[dict[str, Any]]:
    """
    Get the loaded hazard categories, loading config if needed.
    Caches the result for performance.
    
    Returns:
        List of hazard category dictionaries
    """
    global _cached_categories
    
    if _cached_categories is None:
        _cached_categories = load_hazard_config()
    
    return _cached_categories


def reload_config() -> None:
    """
    Force reload of configuration from file.
    Clears the cached prompt and categories.
    """
    global _cached_prompt, _cached_categories
    _cached_prompt = None
    _cached_categories = None
