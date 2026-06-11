"""Tests for hide_features visibility resolution and config parsing."""

import pytest

from neuview.config import Config, HideFeaturesConfig
from neuview.features import (
    FeatureVisibility,
    NEURON_FEATURES,
    LIST_FEATURES,
    NAV_FEATURES,
)


def _config(hide_features=None):
    cfg = {
        "neuprint": {"server": "s", "dataset": "wasp3:v0.8"},
        "output": {"directory": "o"},
    }
    if hide_features is not None:
        cfg["hide_features"] = hide_features
    return Config.from_dict(cfg)


@pytest.mark.unit
class TestFeatureVisibilityDefaults:
    def test_absent_block_shows_everything(self):
        fv = FeatureVisibility.from_config(_config())
        for key in NEURON_FEATURES:
            assert fv.neuron_visible(key)
        for key in LIST_FEATURES:
            assert fv.list_visible(key)

    def test_empty_lists_show_everything(self):
        fv = FeatureVisibility.from_config(_config({"neuron": [], "list": []}))
        assert fv.neuron_visible("connectivity")
        assert fv.list_visible("roi")

    def test_nav_visible_by_default(self):
        fv = FeatureVisibility.from_config(_config())
        for key in NAV_FEATURES:
            assert fv.nav_visible(key)


@pytest.mark.unit
class TestFeatureVisibilityHiding:
    def test_hide_single_neuron_section(self):
        fv = FeatureVisibility.from_config(_config({"neuron": ["connectivity"]}))
        assert fv.neuron_hidden("connectivity")
        assert not fv.neuron_visible("connectivity")
        # Everything else stays visible.
        assert fv.neuron_visible("cards")
        assert fv.neuron_visible("eyemaps")

    def test_visualization_group_expands(self):
        fv = FeatureVisibility.from_config(_config({"neuron": ["visualization"]}))
        assert not fv.neuron_visible("eyemaps")
        assert not fv.neuron_visible("neuroglancer")
        # The group does not hide unrelated sections.
        assert fv.neuron_visible("connectivity")
        assert fv.neuron_visible("layers")

    def test_hide_list_filters(self):
        fv = FeatureVisibility.from_config(
            _config({"list": ["dimorphism", "hemilineage"]})
        )
        assert not fv.list_visible("dimorphism")
        assert not fv.list_visible("hemilineage")
        assert fv.list_visible("roi")
        assert fv.list_visible("side")

    def test_hide_nav_links(self):
        fv = FeatureVisibility.from_config(
            _config({"nav": ["github", "youtube", "neuprint"]})
        )
        assert fv.nav_hidden("github")
        assert not fv.nav_visible("github")
        assert not fv.nav_visible("youtube")
        assert not fv.nav_visible("neuprint")

    def test_hide_nav_partial(self):
        fv = FeatureVisibility.from_config(_config({"nav": ["youtube"]}))
        assert not fv.nav_visible("youtube")
        assert fv.nav_visible("github")
        assert fv.nav_visible("neuprint")

    def test_unknown_names_ignored_with_warning(self, caplog):
        import logging

        # Distinct names so the once-per-process warning cache doesn't swallow them.
        with caplog.at_level(logging.WARNING, logger="neuview.features"):
            fv = FeatureVisibility(
                hidden_neuron=["definitely-not-a-section"],
                hidden_list=["definitely-not-a-filter"],
            )
        # Unknown names hide nothing.
        for key in NEURON_FEATURES:
            assert fv.neuron_visible(key)
        for key in LIST_FEATURES:
            assert fv.list_visible(key)
        text = caplog.text
        assert "definitely-not-a-section" in text
        assert "definitely-not-a-filter" in text


@pytest.mark.unit
class TestHideFeaturesConfigParsing:
    def test_yaml_list_key_maps_to_list_field(self):
        cfg = _config({"neuron": ["cards"], "list": ["roi"], "nav": ["github"]})
        assert isinstance(cfg.hide_features, HideFeaturesConfig)
        assert cfg.hide_features.neuron == ["cards"]
        assert cfg.hide_features.list_ == ["roi"]
        assert cfg.hide_features.nav == ["github"]

    def test_default_is_empty(self):
        cfg = _config()
        assert cfg.hide_features.neuron == []
        assert cfg.hide_features.list_ == []
        assert cfg.hide_features.nav == []
