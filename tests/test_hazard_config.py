"""
Tests for hazard configuration module.
"""

import os
import tempfile
import pytest
from pathlib import Path

from hazard_config import (
    load_hazard_config,
    get_enabled_hazards,
    build_hazard_prompt,
    HazardConfigError,
    DEFAULT_HAZARD_CATEGORIES,
    _validate_config,
    reload_config,
)


class TestDefaultConfig:
    """Tests for default configuration behavior."""

    def test_default_categories_exist(self):
        """Default hazard categories should be defined."""
        assert len(DEFAULT_HAZARD_CATEGORIES) > 0

    def test_default_categories_have_required_fields(self):
        """Each default category should have id, name, description, enabled."""
        for category in DEFAULT_HAZARD_CATEGORIES:
            assert "id" in category
            assert "name" in category
            assert "description" in category
            assert "enabled" in category
            assert isinstance(category["id"], str)
            assert isinstance(category["name"], str)
            assert isinstance(category["description"], str)
            assert isinstance(category["enabled"], bool)

    def test_default_categories_all_enabled(self):
        """All default categories should be enabled by default."""
        for category in DEFAULT_HAZARD_CATEGORIES:
            assert category["enabled"] is True

    def test_default_categories_unique_ids(self):
        """All default category IDs should be unique."""
        ids = [c["id"] for c in DEFAULT_HAZARD_CATEGORIES]
        assert len(ids) == len(set(ids))

    def test_load_returns_defaults_when_no_config_file(self):
        """Loading config without a file should return defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_path = Path(tmpdir) / "nonexistent.yaml"
            categories = load_hazard_config(nonexistent_path)
            assert len(categories) == len(DEFAULT_HAZARD_CATEGORIES)
            for cat, default in zip(categories, DEFAULT_HAZARD_CATEGORIES):
                assert cat["id"] == default["id"]


class TestConfigLoading:
    """Tests for loading configuration from files."""

    def test_load_valid_config(self):
        """Should load a valid YAML config file."""
        config_content = """
hazard_categories:
  - id: test_hazard
    name: Test Hazard
    description: A test hazard for testing
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                categories = load_hazard_config(f.name)
                assert len(categories) == 1
                assert categories[0]["id"] == "test_hazard"
                assert categories[0]["name"] == "Test Hazard"
                assert categories[0]["description"] == "A test hazard for testing"
                assert categories[0]["enabled"] is True
            finally:
                os.unlink(f.name)

    def test_load_config_with_disabled_hazard(self):
        """Should correctly load config with disabled hazards."""
        config_content = """
hazard_categories:
  - id: enabled_hazard
    name: Enabled Hazard
    description: This hazard is enabled
    enabled: true
  - id: disabled_hazard
    name: Disabled Hazard
    description: This hazard is disabled
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                categories = load_hazard_config(f.name)
                assert len(categories) == 2
                enabled = [c for c in categories if c["enabled"]]
                disabled = [c for c in categories if not c["enabled"]]
                assert len(enabled) == 1
                assert len(disabled) == 1
                assert enabled[0]["id"] == "enabled_hazard"
                assert disabled[0]["id"] == "disabled_hazard"
            finally:
                os.unlink(f.name)

    def test_enabled_defaults_to_true(self):
        """If enabled is not specified, it should default to True."""
        config_content = """
hazard_categories:
  - id: no_enabled_field
    name: No Enabled Field
    description: This hazard has no enabled field
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                categories = load_hazard_config(f.name)
                assert len(categories) == 1
                assert categories[0]["enabled"] is True
            finally:
                os.unlink(f.name)


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_missing_hazard_categories_key(self):
        """Should fail if hazard_categories key is missing."""
        config = {"other_key": "value"}
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("hazard_categories" in e for e in errors)

    def test_empty_hazard_categories(self):
        """Should fail if hazard_categories is empty."""
        config = {"hazard_categories": []}
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("empty" in e.lower() for e in errors)

    def test_missing_required_field_id(self):
        """Should fail if id field is missing."""
        config = {
            "hazard_categories": [
                {"name": "Test", "description": "Test description"}
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("id" in e for e in errors)

    def test_missing_required_field_name(self):
        """Should fail if name field is missing."""
        config = {
            "hazard_categories": [
                {"id": "test", "description": "Test description"}
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_missing_required_field_description(self):
        """Should fail if description field is missing."""
        config = {
            "hazard_categories": [
                {"id": "test", "name": "Test"}
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("description" in e for e in errors)

    def test_duplicate_ids(self):
        """Should fail if there are duplicate category IDs."""
        config = {
            "hazard_categories": [
                {"id": "same_id", "name": "First", "description": "First desc"},
                {"id": "same_id", "name": "Second", "description": "Second desc"},
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("duplicate" in e.lower() for e in errors)

    def test_all_hazards_disabled(self):
        """Should fail if all hazards are disabled."""
        config = {
            "hazard_categories": [
                {"id": "test1", "name": "Test 1", "description": "Desc 1", "enabled": False},
                {"id": "test2", "name": "Test 2", "description": "Desc 2", "enabled": False},
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("enabled" in e.lower() for e in errors)

    def test_invalid_enabled_type(self):
        """Should fail if enabled is not a boolean."""
        config = {
            "hazard_categories": [
                {"id": "test", "name": "Test", "description": "Desc", "enabled": "yes"}
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("boolean" in e.lower() for e in errors)

    def test_empty_string_fields(self):
        """Should fail if required string fields are empty."""
        config = {
            "hazard_categories": [
                {"id": "", "name": "Test", "description": "Desc"}
            ]
        }
        errors = _validate_config(config)
        assert len(errors) > 0
        assert any("empty" in e.lower() for e in errors)

    def test_invalid_yaml_raises_error(self):
        """Should raise HazardConfigError for invalid YAML."""
        config_content = """
hazard_categories:
  - id: test
    name: [invalid yaml
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                with pytest.raises(HazardConfigError):
                    load_hazard_config(f.name)
            finally:
                os.unlink(f.name)

    def test_validation_error_raises_exception(self):
        """Should raise HazardConfigError for invalid config."""
        config_content = """
hazard_categories: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                with pytest.raises(HazardConfigError) as exc_info:
                    load_hazard_config(f.name)
                assert "empty" in str(exc_info.value).lower()
            finally:
                os.unlink(f.name)


class TestGetEnabledHazards:
    """Tests for filtering enabled hazards."""

    def test_returns_only_enabled(self):
        """Should return only enabled hazards."""
        categories = [
            {"id": "a", "name": "A", "description": "A desc", "enabled": True},
            {"id": "b", "name": "B", "description": "B desc", "enabled": False},
            {"id": "c", "name": "C", "description": "C desc", "enabled": True},
        ]
        enabled = get_enabled_hazards(categories)
        assert len(enabled) == 2
        assert all(c["enabled"] for c in enabled)
        ids = [c["id"] for c in enabled]
        assert "a" in ids
        assert "c" in ids
        assert "b" not in ids

    def test_defaults_to_enabled_if_missing(self):
        """Should treat missing enabled field as True."""
        categories = [
            {"id": "a", "name": "A", "description": "A desc"},
        ]
        enabled = get_enabled_hazards(categories)
        assert len(enabled) == 1


class TestBuildHazardPrompt:
    """Tests for building the hazard detection prompt."""

    def test_prompt_contains_enabled_hazards(self):
        """Prompt should contain descriptions of enabled hazards."""
        categories = [
            {"id": "a", "name": "A", "description": "Look for hazard A", "enabled": True},
            {"id": "b", "name": "B", "description": "Look for hazard B", "enabled": False},
        ]
        prompt = build_hazard_prompt(categories)
        assert "Look for hazard A" in prompt
        assert "Look for hazard B" not in prompt

    def test_prompt_excludes_disabled_hazards(self):
        """Prompt should not contain descriptions of disabled hazards."""
        categories = [
            {"id": "a", "name": "A", "description": "Enabled hazard description", "enabled": True},
            {"id": "b", "name": "B", "description": "Disabled hazard description", "enabled": False},
        ]
        prompt = build_hazard_prompt(categories)
        assert "Disabled hazard description" not in prompt

    def test_prompt_has_json_structure(self):
        """Prompt should include JSON response structure."""
        categories = [
            {"id": "a", "name": "A", "description": "Test", "enabled": True},
        ]
        prompt = build_hazard_prompt(categories)
        assert "hazard_present" in prompt
        assert "severity" in prompt
        assert "hazard_types" in prompt
        assert "description" in prompt
        assert "recommended_actions" in prompt

    def test_prompt_raises_if_no_enabled(self):
        """Should raise error if no hazards are enabled."""
        categories = [
            {"id": "a", "name": "A", "description": "Test", "enabled": False},
        ]
        with pytest.raises(HazardConfigError):
            build_hazard_prompt(categories)

    def test_default_prompt_matches_original_behavior(self):
        """Default prompt should contain all original hazard categories."""
        prompt = build_hazard_prompt(DEFAULT_HAZARD_CATEGORIES)
        assert "PPE" in prompt or "helmet" in prompt.lower()
        assert "machinery" in prompt.lower() or "forklift" in prompt.lower()
        assert "fall" in prompt.lower()
        assert "fire" in prompt.lower() or "smoke" in prompt.lower()
        assert "exit" in prompt.lower() or "escape" in prompt.lower()


class TestCaching:
    """Tests for configuration caching."""

    def test_reload_clears_cache(self):
        """reload_config should clear the cached values."""
        reload_config()
        from hazard_config import _cached_prompt, _cached_categories
        assert _cached_prompt is None
        assert _cached_categories is None
