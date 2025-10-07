"""
Interactive Scatterplot Service

Simplified service that coordinates other specialized services to create
interactive scatterplot page with plots related to the spatial metrics per type.
"""

import logging
from pathlib import Path
import pandas as pd
from math import ceil, floor, log10, isfinite
from ..result import Result, Ok, Err

from .index_service import IndexService
from .file_service import FileService

logger = logging.getLogger(__name__)

class ScatterplotService:
    """Service for creating scatterplots with markers for all available neuron types."""

    def __init__(self, config, page_generator):
        self.config = config
        self.page_generator = page_generator
        self._batch_neuron_cache = {}

        # Initialize cache manager for neuron type data
        self.cache_manager = None
        if config and hasattr(config, "output") and hasattr(config.output, "directory"):
            from ..cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    async def create_scatterplots(self, command):
        """Create scatterplots of spatial metrics for optic lobe neuron types."""
        output_dir = command.output_directory
        try:
            logger.info("Extracting plot data from cached data")

            # Discover neuron types from cache or file scanning
            neuron_types, _ = IndexService.discover_neuron_types(self, output_dir)
            if not neuron_types:
                return Err("No neuron type HTML files found in output directory")

            # Initialize connector if needed for database lookups
            connector = await IndexService.initialize_connector_if_needed(
                self, neuron_types, output_dir
            )

            # Correct neuron names (convert filenames back to original names)
            corrected_neuron_types, _ = IndexService.correct_neuron_names(
                self, neuron_types, connector
            )

            # Generate scatterplot data for corrected neuron types
            plot_data = self._extract_plot_data(corrected_neuron_types)

            # Within loop for side
            side = "both"

            for region in ["ME", "LO", "LOP"]:
                points = self._extract_points(plot_data, side=side, region=region)
                if not points:
                    raise SystemExit(
                        f"No points found: ensure values exist for types within {side}{region}."
                    )

                ctx = self._prepare(
                    points, axis_gap_px=10, n_cols_region=None, side=side, region=region
                )

                # Use the page generator's Jinja environment
                template = self.page_generator.env.get_template("scatterplot.svg.jinja")
                svg_content = template.render(ctx)

                # Write the index file
                scatter_path = (
                    output_dir / f"{region}_{side}_{command.scatter_filename}"
                )

                with open(scatter_path, "w", encoding="utf-8") as f:
                    f.write(svg_content)

            return

        except Exception as e:
            logger.error(f"Failed to create plot_data: {e}")
            return Err(f"Failed to create plot_data: {str(e)}")

    def _extract_plot_data(self, neuron_types):
        """Generate plot data from list of neuron types.
        Generates the list of dicts containing the spatial metrics
        data used to generate the interactive scatterplots for optic
        lobe cell types. It extracts the relevant data from the
        output/.cache/type.json files generated when making each neuron
        type's respective page."""
        cached_data_lazy = (
            self.cache_manager.get_cached_data_lazy() if self.cache_manager else None
        )
        plot_data = []
        cached_count = 0
        missing_cache_count = 0

        for neuron_type in neuron_types.items():
            # Check if we have cached data for this neuron type
            cache_data = cached_data_lazy.get(neuron_type) if cached_data_lazy else None

            entry = {
                "name": neuron_type,
                "total_count": 0,
                "left_count": 0,
                "right_count": 0,
                "middle_count": 0,
                "undefined_count": 0,
                "has_undefined": False,
                "spatial_metrics": {},
                "roi_summary": {},
            }

            # Use cached data if available
            if cache_data:
                entry["spatial_metrics"] = cache_data.spatial_metrics
                entry["roi_summary"] = cache_data.roi_summary
                entry["total_count"] = cache_data.total_count
                entry["left_count"] = cache_data.soma_side_counts.get("left", 0)
                entry["right_count"] = cache_data.soma_side_counts.get("right", 0)
                entry["middle_count"] = cache_data.soma_side_counts.get("middle", 0)
                entry["undefined_count"] = cache_data.soma_side_counts.get("unknown", 0)
                entry["has_undefined"] = entry["undefined_count"] > 0

                logger.debug(f"Used cached data for {neuron_type}")
                cached_count += 1
            else:
                # No cached data available - use minimal defaults
                logger.debug(f"No cached data available for {neuron_type}")
                missing_cache_count += 1

            plot_data.append(entry)

        # Sort results
        plot_data.sort(key=lambda x: x["name"])

        if missing_cache_count > 0:
            logger.warning(
                f"Plot data generation completed: {len(plot_data)} entries, {cached_count} with cache, {missing_cache_count} missing cache. Run 'quickpage generate' to populate cache."
            )
        else:
            logger.info(
                f"Plot data generation completed: {len(plot_data)} entries, all with cached data"
            )
        return plot_data

    def _extract_points(self, plot_data, side, region):
        """
        Collate the data points required to make the spatial
        metric scatterplots.
        """
        pts = []
        for rec in plot_data:

            # incl = rec.get("roi_summary", {}).get(region, {}).get("incl_scatter")
            # print(incl)

            # # Only include types that have "incl_scatter" == 1.
            # # Pass threshold for syn % and syn #.
            # if incl is not None:
            name = rec.get("name", "unknown")
            x = rec.get("total_count")
            y = (
                rec.get("spatial_metrics", {})
                .get(side, {})
                .get(region, {})
                .get("cell_size")
            )
            c = (
                rec.get("spatial_metrics", {})
                .get(side, {})
                .get(region, {})
                .get("coverage")
            )
            col_count = (
                rec.get("spatial_metrics", {})
                .get(side, {})
                .get(region, {})
                .get("cols_innervated")
            )

            # require x,y positive for log scales
            if x is None or y is None or c is None:
                continue
            try:
                x = float(x)
                y = float(y)
                c = float(c)
            except Exception:
                continue
            if x <= 0 or y <= 0:
                continue

            # Optional data quality filter from prior script
            if col_count is not None:
                try:
                    if float(col_count) <= 9:
                        continue
                except Exception:
                    pass

            pts.append(
                {
                    "name": name,
                    "x": x,
                    "y": y,
                    "coverage": c,
                    "col_count": float(col_count) if col_count is not None else None,
                }
            )
        return pts

    def _prepare(
        self,
        points,
        width=680,
        height=460,
        margins=(60, 72, 64, 72),
        *,
        axis_gap_px=10,
        n_cols_region=None,
        side=None,
        region=None,
    ):
        """Compute pixel positions for an SVG scatter plot (color by coverage)."""
        top, right, bottom, left = margins
        plot_w = width - left - right
        plot_h = height - top - bottom

        side_px = min(plot_w, plot_h)
        plot_w = side_px
        plot_h = side_px

        xmin = min(p["x"] for p in points)
        xmax = max(p["x"] for p in points)
        ymin = min(p["y"] for p in points)
        ymax = max(p["y"] for p in points)

        # expand bounds slightly so dots don't sit on the frame (keep >0)
        pad_x = xmin * 0.05
        pad_y = ymin * 0.08
        xmin = max(1e-12, xmin - pad_x)
        ymin = max(1e-12, ymin - pad_y)
        xmax *= 1.05
        ymax *= 1.08

        lxmin, lxmax = log10(xmin), log10(xmax)
        lymin, lymax = log10(ymin), log10(ymax)
        dx = lxmax - lxmin
        dy = lymax - lymin

        if dx > dy:
            # expand Y range to match X span (around geometric center)
            cy = (lymin + lymax) / 2.0
            lymin, lymax = cy - dx / 2.0, cy + dx / 2.0
            ymin, ymax = 10**lymin, 10**lymax
        elif dy > dx:
            # expand X range to match Y span (around geometric center)
            cx = (lxmin + lxmax) / 2.0
            lxmin, lxmax = cx - dy / 2.0, cx + dy / 2.0
            xmin, xmax = 10**lxmin, 10**lxmax

        # fixed ticks at 1, 10, 100, 1000 (only those within the current axis range)
        xticks = [1, 10, 100, 1000]
        yticks = xticks

        # coverage color scaling with 98th percentile clipping
        coverages = [p["coverage"] for p in points]
        cmin = min(coverages)
        cmax = self._percentile(coverages, 98.0) or max(coverages)
        crng = (cmax - cmin) if isfinite(cmax - cmin) and (cmax - cmin) > 0 else 1.0

        # Inner drawing range to create a visible gap to axes
        inner_x0, inner_x1 = axis_gap_px, max(axis_gap_px, plot_w - axis_gap_px)
        inner_y0, inner_y1 = plot_h - axis_gap_px, axis_gap_px  # inverted

        def sx(v):
            return self._scale_log10(v, xmin, xmax, inner_x0, inner_x1)

        def sy(v):
            return self._scale_log10(v, ymin, ymax, inner_y0, inner_y1)

        for p in points:
            p["sx"] = sx(p["x"])
            p["sy"] = sy(p["y"])  # SVG y grows downward
            # color by coverage (clipped at cmax)
            t_raw = (min(p["coverage"], cmax) - cmin) / crng
            t = max(0.0, min(1.0, t_raw))
            p["color"] = self._cov_to_rgb(t)
            p["r"] = 4
            p["tooltip"] = (
                f"{p['name']} - {region}({side}):\n"
                f" {int(p['x'])} cells:\n"
                f" cell_size: {p['y']:.2f}\n"
                f" coverage: {p['coverage']:.2f}"
            )

        # Reference (anti-diagonal) guide lines under points
        if n_cols_region is None:
            col_counts = [p["col_count"] for p in points if p.get("col_count")]
            if col_counts:
                n_cols_region = max(col_counts)
            else:
                n_cols_region = 10 ** ((log10(xmin * ymin) + log10(xmax * ymax)) / 4)

        multipliers = [0.2, 0.5, 1, 2, 5]

        def guide_width(m):
            if m < 0.5 or m > 2:
                return 0.25
            elif m != 1:
                return 0.4
            else:
                return 0.8

        guide_lines = []
        for m in multipliers:
            k = n_cols_region * m  # x*y = k
            x0_clip = max(xmin, k / ymax)
            x1_clip = min(xmax, k / ymin)
            if x0_clip >= x1_clip:
                continue  # out of view
            y0 = k / x0_clip
            y1 = k / x1_clip
            guide_lines.append(
                {
                    "x1": sx(x0_clip),
                    "y1": sy(y0),
                    "x2": sx(x1_clip),
                    "y2": sy(y1),
                    "w": guide_width(m),
                }
            )

        # Precompute pixel tick positions for Jinja (avoid math inside template)
        def log_pos_x(t):
            return self._scale_log10(t, xmin, xmax, inner_x0, inner_x1)

        def log_pos_y(t):
            return self._scale_log10(t, ymin, ymax, inner_y0, inner_y1)

        xtick_data = [{"t": t, "px": log_pos_x(t)} for t in xticks]
        ytick_data = [{"t": t, "py": log_pos_y(t)} for t in yticks]

        ctx = {
            "width": width,
            "height": height,
            "margin_top": top,
            "margin_right": right,
            "margin_bottom": bottom,
            "margin_left": left,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "xticks": xticks,
            "yticks": yticks,
            "xmin": xmin,
            "xmax": xmax,
            "ymin": ymin,
            "ymax": ymax,
            "cmin": cmin,
            "cmax": cmax,
            "points": points,
            "title": f"{region}({side}): total_count vs cell_size",
            "subtitle": "colorscale = coverage (max at 98th percentile)",
            "xtick_data": xtick_data,
            "ytick_data": ytick_data,
            "guide_lines": guide_lines,
            "xlabel": "Population size (no. cells per type)",
            "ylabel": "Cell size (no. columns per cell)",
        }

        return ctx

    def _log_ticks(self, vmin, vmax):
        """Ticks for a log10 axis between (vmin, vmax), inclusive."""
        if vmin <= 0 or vmax <= 0 or vmin >= vmax:
            return []
        lo = floor(log10(vmin))
        hi = ceil(log10(vmax))
        return [10**e for e in range(lo, hi + 1)]

    def _scale_log10(self, v, vmin, vmax, a, b):
        """Log10 scaling to pixels."""
        lv = log10(v)
        lmin = log10(vmin)
        lmax = log10(vmax)
        if lmax == lmin:
            return (a + b) / 2.0
        return a + (lv - lmin) * (b - a) / (lmax - lmin)

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def _cov_to_rgb(self, t):
        """
        Map t in [0,1] to a white→dark red gradient.
        start = white (255,255,255), end = dark red (~180,0,0)
        """
        r0, g0, b0 = 255, 255, 255
        r1, g1, b1 = 180, 0, 0
        r = int(round(self._lerp(r0, r1, t)))
        g = int(round(self._lerp(g0, g1, t)))
        b = int(round(self._lerp(b0, b1, t)))
        return f"rgb({r},{g},{b})"

    def _percentile(self, values, p):
        """
        p in [0, 100]. Returns None on no finite data.
        Uses pandas.Series.quantile with the right keyword for the installed version.
        """
        s = pd.Series(values, dtype="float64").dropna()
        if s.empty:
            return None

        q = p / 100
        # Prefer the 2.x API if available; fall back to 1.5.x
        try:
            return float(s.quantile(q, method="linear"))  # pandas 2.x
        except TypeError:
            return float(s.quantile(q, interpolation="linear"))  # pandas 1.5.x
