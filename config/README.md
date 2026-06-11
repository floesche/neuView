# neuView dataset configuration

Each `config.<dataset>.yaml` file configures one NeuPrint dataset (server,
dataset name, output, discovery, neuroglancer template, HTML metadata, subsets).
This document describes the optional **`hide_features`** block.

## `hide_features`

Hide individual sections of the neuron pages and individual filters of the
types list, per dataset.

```yaml
hide_features:
  neuron: ["visualization"]
  nav: ["github", "youtube"]
  list: ["dimorphism", "hemilineage"]
```

**Semantics — listed means hidden.** Anything you list is hidden; anything you
do not list stays visible. A missing block, a missing key, or an empty list
therefore shows *as much as possible*:

| Config | Result |
| --- | --- |
| no `hide_features` block | everything visible |
| `neuron: []` (or key absent) | all neuron sections visible |
| `neuron: ["connectivity"]` | every neuron section **except** connectivity |

Unknown names are ignored with a warning (logged once per run), so a typo
disables nothing silently — check the logs if a feature you expected to hide is
still showing.

When a feature is hidden its **data is removed** from the page, not just hidden
with CSS: the section/filter and its supporting data (e.g. the matching tags on
the type cards, the hamburger-menu link) are not rendered.

### `neuron:` — sections of an individual neuron page

| Key | Hides |
| --- | --- |
| `cards` | Summary statistics cards (counts, synapses, …) |
| `layers` | "Mean Synapse Count per Layer" section |
| `eyemaps` | "Population Spatial Coverage" hexagon maps |
| `neuroglancer` | "Neuron Visualization" (embedded Neuroglancer) |
| `innervation` | "ROI Innervation" section |
| `connectivity` | Upstream/downstream connectivity tables |

Group shortcut (expands to several keys):

| Group | Expands to |
| --- | --- |
| `visualization` | `eyemaps`, `neuroglancer` |

### `nav:` — external service links

Hides every link to the named service across **all** pages (header bar,
hamburger menu, the GitHub feedback button, the per-neuron neuPrint link, the
per-neuron YouTube video link, and the contextual links on the index/help
pages). Prose mentions of the service name are kept; only the hyperlinks are
removed.

| Key | Hides links to |
| --- | --- |
| `github` | GitHub repository links + the feedback button (opens a GitHub issue) |
| `youtube` | YouTube channel link + per-neuron video links |
| `neuprint` | NeuPrint dataset links + the per-neuron "open in neuPrint" link |

### `list:` — filters/tags of the types list page

Each key hides both the filter dropdown and the matching tag on the type cards.

| Key | Hides |
| --- | --- |
| `roi` | ROI (brain region) filter + ROI tags |
| `neurotransmitter` | Neurotransmitter filter + NT tag |
| `dimorphism` | Dimorphism filter + tag |
| `side` | Side filter + the "only L/R/M / Undefined" indicators |
| `superclass` | Superclass filter + tag |
| `class` | Class filter + tag |
| `subclass` | Subclass filter + tag |
| `region` | Region filter + parent-region tags |
| `count` | Cell-count filter + count tag |
| `neuromere` | Soma-neuromere filter + tag |
| `hemilineage` | Truman-hemilineage filter + tag |

Note: hiding `side` or `count` removes only the *filter and tags*; the per-side
page links and cell-count totals shown in card titles/tooltips are core
navigation and remain.

### Example

```yaml
# A visual-system dataset that has no dimorphism or hemilineage annotation
# and no embedded Neuroglancer view:
hide_features:
  neuron: ["neuroglancer"]
  list: ["dimorphism", "hemilineage", "neuromere"]
```
