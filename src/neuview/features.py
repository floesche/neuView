"""
Feature visibility for per-dataset page customization.

Datasets can hide individual sections of the neuron pages and individual
filters of the types list via the ``hide_features`` config block::

    hide_features:
      neuron: ["visualization"]
      list: ["dimorphism", "hemilineage"]

Semantics: anything *listed* is hidden; anything not listed stays visible. A
missing or empty list therefore shows as much as possible. Unknown names are
ignored with a warning (see ``config/README.md`` for the full key list).
"""

import logging
from typing import Iterable, Set

logger = logging.getLogger(__name__)

# Canonical neuron-page section feature keys.
NEURON_FEATURES: Set[str] = {
    "cards",  # summary statistics cards
    "layers",  # mean synapse count per layer
    "eyemaps",  # population spatial coverage hex maps
    "neuroglancer",  # 3D neuron visualization (Neuroglancer)
    "innervation",  # ROI innervation
    "connectivity",  # upstream/downstream connectivity tables
}

# Convenience groups that expand to several neuron section keys.
NEURON_FEATURE_GROUPS = {
    "visualization": frozenset({"eyemaps", "neuroglancer"}),
}

# Canonical navigation-link feature keys (external links shown as site chrome
# and per-page service links).
NAV_FEATURES: Set[str] = {
    "github",  # GitHub repository / feedback links
    "youtube",  # YouTube channel and per-neuron video links
    "neuprint",  # NeuPrint dataset / per-neuron links
}

# Canonical types-list filter feature keys.
LIST_FEATURES: Set[str] = {
    "roi",
    "neurotransmitter",
    "dimorphism",
    "side",
    "superclass",
    "class",
    "subclass",
    "region",
    "count",
    "neuromere",
    "hemilineage",
}

# Track unknown names already warned about, so a misconfiguration logs once per
# process instead of once per generated page.
_warned: Set[str] = set()


def _warn_once(message: str) -> None:
    if message not in _warned:
        _warned.add(message)
        logger.warning(message)


class FeatureVisibility:
    """Resolves which page features are visible for the current dataset.

    Built from the ``hide_features`` config block. Exposes ``*_visible`` methods
    for templates (Jinja-friendly) and ``*_hidden`` methods for Python callers
    that strip data for hidden features.
    """

    def __init__(
        self,
        hidden_neuron: Iterable[str] = (),
        hidden_list: Iterable[str] = (),
        hidden_nav: Iterable[str] = (),
    ):
        self._hidden_neuron = self._resolve_neuron(hidden_neuron)
        self._hidden_list = self._resolve_list(hidden_list)
        self._hidden_nav = self._resolve_nav(hidden_nav)

    @classmethod
    def from_config(cls, config) -> "FeatureVisibility":
        """Build from a Config object's ``hide_features`` block (if any)."""
        hide_features = getattr(config, "hide_features", None)
        if hide_features is None:
            return cls()
        return cls(
            hidden_neuron=getattr(hide_features, "neuron", ()) or (),
            hidden_list=getattr(hide_features, "list_", ()) or (),
            hidden_nav=getattr(hide_features, "nav", ()) or (),
        )

    @staticmethod
    def _resolve_neuron(names: Iterable[str]) -> Set[str]:
        hidden: Set[str] = set()
        for name in names or ():
            if name in NEURON_FEATURE_GROUPS:
                hidden |= set(NEURON_FEATURE_GROUPS[name])
            elif name in NEURON_FEATURES:
                hidden.add(name)
            else:
                _warn_once(
                    f"Unknown hide_features.neuron entry '{name}' (ignored). "
                    f"Valid keys: {sorted(NEURON_FEATURES)}; "
                    f"groups: {sorted(NEURON_FEATURE_GROUPS)}"
                )
        return hidden

    @staticmethod
    def _resolve_list(names: Iterable[str]) -> Set[str]:
        hidden: Set[str] = set()
        for name in names or ():
            if name in LIST_FEATURES:
                hidden.add(name)
            else:
                _warn_once(
                    f"Unknown hide_features.list entry '{name}' (ignored). "
                    f"Valid keys: {sorted(LIST_FEATURES)}"
                )
        return hidden

    @staticmethod
    def _resolve_nav(names: Iterable[str]) -> Set[str]:
        hidden: Set[str] = set()
        for name in names or ():
            if name in NAV_FEATURES:
                hidden.add(name)
            else:
                _warn_once(
                    f"Unknown hide_features.nav entry '{name}' (ignored). "
                    f"Valid keys: {sorted(NAV_FEATURES)}"
                )
        return hidden

    # -- Template-facing (Jinja) -------------------------------------------
    def neuron_visible(self, key: str) -> bool:
        """True if the given neuron-page section should be rendered."""
        return key not in self._hidden_neuron

    def list_visible(self, key: str) -> bool:
        """True if the given types-list filter/tag should be rendered."""
        return key not in self._hidden_list

    def nav_visible(self, key: str) -> bool:
        """True if links to the given external service should be rendered."""
        return key not in self._hidden_nav

    # -- Python-facing ------------------------------------------------------
    def neuron_hidden(self, key: str) -> bool:
        return key in self._hidden_neuron

    def list_hidden(self, key: str) -> bool:
        return key in self._hidden_list

    def nav_hidden(self, key: str) -> bool:
        return key in self._hidden_nav
