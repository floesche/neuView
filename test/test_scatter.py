# scatter_svg_from_plot_data.py (updated)
from math import ceil, floor, log10, isfinite
from jinja2 import Template
import pickle

file_path = 'my_file.pkl'
with open(file_path, 'rb') as f:
    plot_data = pickle.load(f)


def extract_points(records, side, region):
    """
    Collect points, requiring:
      - total_count (x) > 0
      - cell_size (y) > 0  from spatial_metrics[side][region].cell_size
      - coverage (c) present and >= 0 (used only for color scale)
    Also retain cols_innervated for reference lines.
    """
    pts = []
    for rec in records:
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

        pts.append({
            "name": name,
            "x": x,
            "y": y,
            "coverage": c,
            "col_count": float(col_count) if col_count is not None else None,
        })
    return pts


def log_ticks(vmin, vmax):
    """Decade ticks for a log10 axis between (vmin, vmax), inclusive."""
    if vmin <= 0 or vmax <= 0 or vmin >= vmax:
        return []
    lo = floor(log10(vmin))
    hi = ceil(log10(vmax))
    return [10 ** e for e in range(lo, hi + 1)]


def scale_log10(v, vmin, vmax, a, b):
    """Log10 scaling to pixels."""
    lv = log10(v)
    lmin = log10(vmin)
    lmax = log10(vmax)
    if lmax == lmin:
        return (a + b) / 2.0
    return a + (lv - lmin) * (b - a) / (lmax - lmin)


def lerp(a, b, t):
    return a + (b - a) * t


def cov_to_rgb(t):
    """
    Map t in [0,1] to a white→dark red gradient.
    start = white (255,255,255), end = dark red (~180,0,0)
    """
    r0, g0, b0 = 255, 255, 255
    r1, g1, b1 = 150, 0, 0
    r = int(round(lerp(r0, r1, t)))
    g = int(round(lerp(g0, g1, t)))
    b = int(round(lerp(b0, b1, t)))
    return f"rgb({r},{g},{b})"


def percentile(values, p):
    """Return the p-th percentile (0-100) with linear interpolation, pure Python."""
    vals = sorted(v for v in values if v is not None)
    n = len(vals)
    if n == 0:
        return None
    if n == 1:
        return vals[0]
    # rank in [0, n-1]
    r = (p / 100.0) * (n - 1)
    lo = int(r)
    hi = min(lo + 1, n - 1)
    t = r - lo
    return vals[lo] * (1 - t) + vals[hi] * t


def prepare(points, width=680, height=460, margins=(60, 72, 64, 72), *, axis_gap_px=10, n_cols_region=None, side=None, region=None):
    """Compute pixel positions for an SVG scatter plot (log–log, color by coverage).

    Changes vs. prior version:
      - Adds an inner pixel gap (axis_gap_px) so points do not touch the axes.
      - Removes the plot "box" (background rect) in the template.
      - Adds five light-grey guide lines (below points) for k = n_cols_region × {0.2,0.5,1,2,5}
        where the guides follow x*y = k (straight anti-diagonals in log–log).
        If n_cols_region is None, it is estimated as the max of available `col_count`.
      - Sets color max to the 98th percentile of coverage values (legend reflects this clip).
      - Adds axis labels for X and Y.
    """
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
        ymin, ymax = 10 ** lymin, 10 ** lymax
    elif dy > dx:
        # expand X range to match Y span (around geometric center)
        cx = (lxmin + lxmax) / 2.0
        lxmin, lxmax = cx - dy / 2.0, cx + dy / 2.0
        xmin, xmax = 10 ** lxmin, 10 ** lxmax

    # fixed ticks at 1, 10, 100, 1000 (only those within the current axis range)
    xticks = [1, 10, 100, 1000]
    yticks = xticks

    # coverage color scaling with 98th percentile clipping
    coverages = [p["coverage"] for p in points]
    cmin = min(coverages)
    cmax = percentile(coverages, 98.0) or max(coverages)
    crng = (cmax - cmin) if isfinite(cmax - cmin) and (cmax - cmin) > 0 else 1.0

    # Inner drawing range to create a visible gap to axes
    inner_x0, inner_x1 = axis_gap_px, max(axis_gap_px, plot_w - axis_gap_px)
    inner_y0, inner_y1 = plot_h - axis_gap_px, axis_gap_px  # inverted

    def sx(v):
        return scale_log10(v, xmin, xmax, inner_x0, inner_x1)

    def sy(v):
        return scale_log10(v, ymin, ymax, inner_y0, inner_y1)

    for p in points:
        p["sx"] = sx(p["x"])
        p["sy"] = sy(p["y"])  # SVG y grows downward
        # color by coverage (clipped at cmax)
        t_raw = (min(p["coverage"], cmax) - cmin) / crng
        t = max(0.0, min(1.0, t_raw))
        p["color"] = cov_to_rgb(t)
        p["r"] = 4
        p["tooltip"] = (
            f"{p['name']} - {region}({side}):\n"
            f" {int(p['x'])} cells:\n"
            f" cell_size: {p['y']:.3f}\n"
            f" coverage: {p['coverage']:.3f}"
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
        # Clip hyperbola segment to the [xmin,xmax]×[ymin,ymax] window in data space
        x0_clip = max(xmin, k / ymax)
        x1_clip = min(xmax, k / ymin)
        if x0_clip >= x1_clip:
            continue  # out of view
        y0 = k / x0_clip
        y1 = k / x1_clip
        guide_lines.append({
            "x1": sx(x0_clip),
            "y1": sy(y0),
            "x2": sx(x1_clip),
            "y2": sy(y1),
            "w": guide_width(m),
        })

    # Precompute pixel tick positions for Jinja (avoid math inside template)
    def log_pos_x(t):
        return scale_log10(t, xmin, xmax, inner_x0, inner_x1)

    def log_pos_y(t):
        return scale_log10(t, ymin, ymax, inner_y0, inner_y1)

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
        "xmin": xmin, "xmax": xmax,
        "ymin": ymin, "ymax": ymax,
        "cmin": cmin, "cmax": cmax,
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

SVG_TEMPLATE = Template(r"""
<svg
  width="{{ width }}"
  height="{{ height }}"
  viewBox="0 0 {{ width }} {{ height }}"
  xmlns="http://www.w3.org/2000/svg"
>
<defs>
  <style>
    .axis-line { stroke:#444; stroke-width:1; shape-rendering:crispEdges; }
    .tick-mark { stroke:#444; stroke-width:1; shape-rendering:crispEdges; }
    .tick-label { fill:#444; font-size:14px; font-family:Helvetica, Arial, sans-serif; }
    .title { fill:#333; font-size:14px; font-family:Arial, sans-serif; }
    .subtitle { fill:#777; font-size:11px; font-family:Arial, sans-serif; }
    .axis-label { fill:#333; font-size:16px; font-family:Helvetica, Arial, sans-serif; }
    .dot { cursor:pointer; opacity:0.9; transition:opacity 0.15s; }
    .dot:hover { opacity:1; }
    .tooltip-box { pointer-events:none; transition:opacity 0.15s; }
    .tooltip-bg { fill:rgba(0,0,0,0.8); rx:3; ry:3; }
    .tooltip-text { fill:#fff; font-size:12px; font-family:Helvetica, Arial, sans-serif; }
    .legend-label { fill:#555; font-size:14px; font-family:Helvetica, Arial, sans-serif; }
    .legend-title { fill:#555; font-size:14px; font-family:Helvetica, Arial, sans-serif; }
    .guide { stroke: #bfbfbf; fill: none; }
  </style>
</defs>

<script type="text/ecmascript">
//<![CDATA[
function showTip(evt) {
  const svg = evt.currentTarget.ownerSVGElement;
  const tip = svg.getElementById("tooltip");
  const g = evt.currentTarget;
  const c = g.querySelector("circle");

  const base = parseFloat(c.getAttribute("data-base-r") || "4");
  c.setAttribute("r", String(base * 1.8));

  const text = c.getAttribute("data-title") || "";
  if (!text) return;

  const lines = text.split("\n").filter(s => s.trim().length);
  const tg = svg.getElementById("tooltip-text-group");
  while (tg.firstChild) tg.removeChild(tg.firstChild);

  const pad = 6, lh = 14;
  let maxW = 0;
  for (let i = 0; i < lines.length; i++) {
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", pad);
    t.setAttribute("y", pad + lh + i * lh);
    t.setAttribute("class", "tooltip-text");
    t.textContent = lines[i];
    tg.appendChild(t);
    const approx = lines[i].length * 6.5;
    if (approx > maxW) maxW = approx;
  }

  const rect = svg.getElementById("tooltip-bg");
  const boxW = Math.max(maxW + pad * 2, 140);
  const boxH = lines.length * lh + pad * 2;
  rect.setAttribute("width", boxW);
  rect.setAttribute("height", boxH);

  const bounds = svg.getBoundingClientRect();
  let x = evt.clientX - bounds.left + 10;
  let y = evt.clientY - bounds.top  - boxH - 10;
  if (x + boxW > {{ width }}) x = {{ width }} - boxW - 5;
  if (y < 0) y = evt.clientY - bounds.top + 10;
  if (x < 0) x = 5;

  tip.setAttribute("transform", "translate(" + x + "," + y + ")");
  tip.setAttribute("opacity", "1");

  const tEl = g.querySelector("title");
  if (tEl) tEl.textContent = "";
}

function hideTip(evt) {
  const svg = evt.currentTarget.ownerSVGElement;
  const tip = svg.getElementById("tooltip");
  tip.setAttribute("opacity", "0");

  const g = evt.currentTarget;
  const c = g.querySelector("circle");
  const base = parseFloat(c.getAttribute("data-base-r") || "4");
  c.setAttribute("r", String(base));

  const text = c.getAttribute("data-title") || "";
  const tEl = g.querySelector("title");
  if (tEl) tEl.textContent = text;
}
//]]>
</script>

<!-- Plot area -->
<g id="scatter"
   transform="translate({{ margin_left }}, {{ margin_top }})">

  <!-- axis baselines (kept) -->
  <line class="axis-line" x1="0" y1="{{ plot_h }}" x2="{{ plot_w }}" y2="{{ plot_h }}" />
  <line class="axis-line" x1="0" y1="0" x2="0" y2="{{ plot_h }}" />

  <!-- ticks (X) — outward -->
  {% for tick in xtick_data %}
  <line class="tick-mark" x1="{{ tick.px }}" y1="{{ plot_h }}" x2="{{ tick.px }}" y2="{{ plot_h + 6 }}" />
  <text class="tick-label" x="{{ tick.px }}" y="{{ plot_h + 18 }}" text-anchor="middle">
    {{ tick.t }}
  </text>
  {% endfor %}

  <!-- ticks (Y) — outward -->
  {% for tick in ytick_data %}
  <line class="tick-mark" x1="0" y1="{{ tick.py }}" x2="-6" y2="{{ tick.py }}" />
  <text class="tick-label" x="-8" y="{{ tick.py + 4 }}" text-anchor="end">
    {{ tick.t }}
  </text>
  {% endfor %}

  <!-- light grey guide lines (under points) -->
  {% for g in guide_lines %}
  <line class="guide" x1="{{ g.x1 }}" y1="{{ g.y1 }}" x2="{{ g.x2 }}" y2="{{ g.y2 }}" stroke-width="{{ g.w }}" />
  {% endfor %}

  <!-- markers -->
  {% for p in points %}
  <g class="marker" transform="translate({{ p.sx }}, {{ p.sy }})" onmouseover="showTip(event)" onmouseout="hideTip(event)">
    <circle r="{{ p.r }}" data-base-r="{{ p.r }}" class="dot" data-title="{{ p.tooltip | e }}" fill="{{ p.color }}" stroke="#000" stroke-width="0.5">
      <title>{{ p.tooltip }}</title>
    </circle>
  </g>
  {% endfor %}
</g>

<!-- Axis labels -->
<text class="axis-label" text-anchor="middle" x="{{ margin_left + plot_w/2 }}" y="{{ margin_top + plot_h + 40 }}">{{ xlabel }}</text>
<text class="axis-label" text-anchor="middle" transform="translate(20, {{ margin_top + plot_h/2 }}) rotate(-90)">{{ ylabel }}</text>

<!-- vertical color legend at right of plot -->
  <g transform="translate({{ margin_left + plot_w + 12 }}, {{ margin_top }})">
    <defs>
      <linearGradient id="covGradV" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stop-color="rgb(180,0,0)" />
        <stop offset="100%" stop-color="rgb(255,255,255)" />
      </linearGradient>
    </defs>
    <text class="legend-title" text-anchor="middle"
          transform="translate(30, {{ plot_h/2 }}) rotate(-90)">
      Coverage factor (cells per column)
    </text>
    <rect x="0" y="0" width="12" height="{{ plot_h }}" fill="url(#covGradV)" stroke="#ccc" stroke-width="0.5" />
    <!-- max at top, min at bottom -->
    <text class="legend-label" x="16" y="10" text-anchor="start">>{{ '%.0f' % cmax }}</text>
    <text class="legend-label" x="16" y="{{ plot_h - 2 }}" text-anchor="start">{{ '%.0f' % cmin }}</text>
  </g>

  <!-- tooltip (top layer) -->
<g id="tooltip" class="tooltip-box" opacity="0">
  <rect id="tooltip-bg" class="tooltip-bg" width="140" height="40" />
  <g id="tooltip-text-group"></g>
</g>
</svg>
""", trim_blocks=True, lstrip_blocks=True)

# Jinja helper registrations
# SVG_TEMPLATE.globals.update(fmt_decade=fmt_decade)

if __name__ == "__main__":
    side = "R"
    region = "LOP"

    points = extract_points(plot_data, side=side, region=region)
    if not points:
        raise SystemExit("No points found: ensure R→ME cell_size values exist and x,y > 0.")
    
    ctx = prepare(points, axis_gap_px=10, n_cols_region=None, side=side, region=region)

    svg = SVG_TEMPLATE.render(**ctx)
    with open(f"scatter_{side}_{region}.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Wrote scatter_{side}_{region}.svg")
