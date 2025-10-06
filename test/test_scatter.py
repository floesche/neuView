# scatter_svg_from_plot_data.py
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
        pts.append({"name": name, "x": x, "y": y, "coverage": c})
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
    r1, g1, b1 = 255, 0, 0
    r = int(round(lerp(r0, r1, t)))
    g = int(round(lerp(g0, g1, t)))
    b = int(round(lerp(b0, b1, t)))
    return f"rgb({r},{g},{b})"

def prepare(points, width=680, height=440, margins=(60, 24, 44, 64)):
    """Compute pixel positions for an SVG scatter plot (log–log, color by coverage)."""
    top, right, bottom, left = margins
    plot_w = width - left - right
    plot_h = height - top - bottom

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

    # ticks (log decades)
    xticks = log_ticks(xmin, xmax)
    yticks = log_ticks(ymin, ymax)

    # coverage color scaling
    cmin = min(p["coverage"] for p in points)
    cmax = max(p["coverage"] for p in points)
    crng = (cmax - cmin) if isfinite(cmax - cmin) and (cmax - cmin) > 0 else 1.0

    for p in points:
        p["sx"] = scale_log10(p["x"], xmin, xmax, 0, plot_w)
        p["sy"] = scale_log10(p["y"], ymin, ymax, plot_h, 0)  # invert later via SVG coords
        # color by coverage
        t = (p["coverage"] - cmin) / crng
        p["color"] = cov_to_rgb(max(0.0, min(1.0, t)))
        p["r"] = 4
        p["tooltip"] = (
            f"{p['name']}\n"
            f"count: {int(p['x'])}\n"
            f"L→ME cell_size: {p['y']:.3f}\n"
            f"coverage: {p['coverage']:.3f}"
        )

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
        "title": "L → ME: total_count vs cell_size (log–log)",
        "subtitle": "color = coverage (blue→red)",
    }

     # Precompute pixel tick positions for Jinja (avoid math inside template)
    def log_pos_x(t):
        return scale_log10(t, xmin, xmax, 0, plot_w)
    def log_pos_y(t):
        return scale_log10(t, ymin, ymax, plot_h, 0)

    xtick_data = [{"t": t, "px": log_pos_x(t)} for t in xticks]
    ytick_data = [{"t": t, "py": log_pos_y(t)} for t in yticks]

    ctx.update({
        "xtick_data": xtick_data,
        "ytick_data": ytick_data,
    })

    return ctx

def fmt_decade(v):
    """Format decade tick as 10^n, fallback to number if not exact."""
    try:
        e = round(log10(v))
        if abs((10**e) - v) / v < 1e-9:
            return f"10^{e}"
    except Exception:
        pass
    return f"{v:g}"

SVG_TEMPLATE = Template(r"""
<svg
  width="{{ width }}"
  height="{{ height }}"
  viewBox="0 0 {{ width }} {{ height }}"
  xmlns="http://www.w3.org/2000/svg"
>
<defs>
  <style>
    .plot-bg { fill:#ffffff; stroke:#cccccc; }
    .axis-line { stroke:#444; stroke-width:1; shape-rendering:crispEdges; }
    .tick-mark { stroke:#444; stroke-width:1; shape-rendering:crispEdges; }
    .tick-label { fill:#444; font-size:11px; font-family:Helvetica, Arial, sans-serif; }
    .title { fill:#333; font-size:13px; font-family:Arial, sans-serif; }
    .subtitle { fill:#777; font-size:11px; font-family:Arial, sans-serif; }
    .dot { cursor:pointer; opacity:0.9; transition:opacity 0.15s; }
    .dot:hover { opacity:1; }
    .tooltip-box { pointer-events:none; transition:opacity 0.15s; }
    .tooltip-bg { fill:rgba(0,0,0,0.8); rx:3; ry:3; }
    .tooltip-text { fill:#fff; font-size:12px; font-family:Helvetica, Arial, sans-serif; }
    .legend-label { fill:#555; font-size:10px; font-family:Helvetica, Arial, sans-serif; }
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

<!-- Titles -->
<text x="8" y="16" class="title">{{ title }}</text>
<text x="8" y="32" class="subtitle">{{ subtitle }}</text>

<!-- Plot area -->
<g id="scatter"
   transform="translate({{ margin_left }}, {{ margin_top }})">
  <rect class="plot-bg" x="0" y="0" width="{{ plot_w }}" height="{{ plot_h }}" />

  <!-- axis baselines -->
  <line class="axis-line" x1="0" y1="{{ plot_h }}" x2="{{ plot_w }}" y2="{{ plot_h }}" />
  <line class="axis-line" x1="0" y1="0" x2="0" y2="{{ plot_h }}" />

 <!-- ticks (X) — outward -->
  {% for tick in xtick_data %}
  <line class="tick-mark" x1="{{ tick.px }}" y1="{{ plot_h }}" x2="{{ tick.px }}" y2="{{ plot_h + 6 }}" />
  <text class="tick-label" x="{{ tick.px }}" y="{{ plot_h + 18 }}" text-anchor="middle">
    {{ fmt_decade(tick.t) }}
  </text>
  {% endfor %}

  <!-- ticks (Y) — outward -->
  {% for tick in ytick_data %}
  <line class="tick-mark" x1="0" y1="{{ tick.py }}" x2="-6" y2="{{ tick.py }}" />
  <text class="tick-label" x="-8" y="{{ tick.py + 4 }}" text-anchor="end">
    {{ fmt_decade(tick.t) }}
  </text>
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

<!-- simple color legend -->
<g transform="translate({{ margin_left + 10 }}, {{ height - 16 }})">
  <defs>
    <linearGradient id="covGrad" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0%"  stop-color="rgb(255,255,255)" />
    <stop offset="100%" stop-color="rgb(180,0,0)" />
  </linearGradient>
  </defs>
  <rect x="0" y="-10" width="120" height="8" fill="url(#covGrad)" />
  <text class="legend-label" x="0" y="0">coverage: {{ '%.3f' % cmin }}</text>
  <text class="legend-label" x="120" y="0" text-anchor="end">{{ '%.3f' % cmax }}</text>
</g>

<!-- tooltip (top layer) -->
<g id="tooltip" class="tooltip-box" opacity="0">
  <rect id="tooltip-bg" class="tooltip-bg" width="140" height="40" />
  <g id="tooltip-text-group"></g>
</g>
</svg>
""", trim_blocks=True, lstrip_blocks=True)

# Jinja helper registrations
SVG_TEMPLATE.globals.update(fmt_decade=fmt_decade)

if __name__ == "__main__":
    side = "R"
    region = "ME"
    points = extract_points(plot_data, side=side, region=region)
    if not points:
        raise SystemExit("No points found: ensure R→ME cell_size values exist and x,y > 0.")
    ctx = prepare(points)
    svg = SVG_TEMPLATE.render(**ctx)
    with open(f"scatter_{side}_{region}.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote scatter_{side}_{region}.svg")