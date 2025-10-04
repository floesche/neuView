
# scatter_svg_from_plot_data.py
from math import ceil, floor
from jinja2 import Template

plot_data = [{'name': 'ANXXX006', 'total_count': 2, 'left_count': 1, 'right_count': 1, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'AVLP370_a', 'total_count': 2, 'left_count': 1, 'right_count': 1, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'AVLP447', 'total_count': 2, 'left_count': 1, 'right_count': 1, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'C3', 'total_count': 1779, 'left_count': 887, 'right_count': 892, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 880, 'coverage': 6.196590909090909, 'cell_size': 6.0}, 'LO': {'cols_innervated': 2, 'coverage': 1.5, 'cell_size': 1.5}, 'LOP': {'cols_innervated': 2, 'coverage': 1.0, 'cell_size': 1.0}}, 'R': {'ME': {'cols_innervated': 892, 'coverage': 6.36322869955157, 'cell_size': 6.0}, 'LO': {'cols_innervated': 3, 'coverage': 1.0, 'cell_size': 1.5}, 'LOP': {'cols_innervated': 3, 'coverage': 1.0, 'cell_size': 1.0}}, 'both': {'ME': {'cols_innervated': 886.0, 'coverage': 6.279909804321239, 'cell_size': 6.0}, 'LO': {'cols_innervated': 2.5, 'coverage': 1.25, 'cell_size': 1.5}, 'LOP': {'cols_innervated': 2.5, 'coverage': 1.0, 'cell_size': 1.0}}}}, {'name': 'CB3417', 'total_count': 10, 'left_count': 5, 'right_count': 5, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'Dm12', 'total_count': 276, 'left_count': 139, 'right_count': 137, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 880, 'coverage': 4.795454545454546, 'cell_size': 30.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 892, 'coverage': 4.996636771300448, 'cell_size': 31.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 10, 'coverage': 1.0, 'cell_size': 10.0}}, 'both': {'ME': {'cols_innervated': 886.0, 'coverage': 4.896045658377497, 'cell_size': 30.5}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 5.0, 'coverage': 1.0, 'cell_size': 10.0}}}}, {'name': 'Dm4', 'total_count': 99, 'left_count': 51, 'right_count': 48, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 876, 'coverage': 1.6232876712328768, 'cell_size': 27.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 890, 'coverage': 1.5853932584269663, 'cell_size': 29.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 883.0, 'coverage': 1.6043404648299215, 'cell_size': 28.0}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'Dm9', 'total_count': 273, 'left_count': 138, 'right_count': 135, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 853, 'coverage': 2.7960140679953107, 'cell_size': 18.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 885, 'coverage': 3.218079096045198, 'cell_size': 21.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 869.0, 'coverage': 3.007046582020254, 'cell_size': 19.5}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'IN01B041', 'total_count': 4, 'left_count': 2, 'right_count': 2, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'IN01B099', 'total_count': 4, 'left_count': 2, 'right_count': 2, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'IN19B107', 'total_count': 2, 'left_count': 1, 'right_count': 1, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'IN23B083', 'total_count': 2, 'left_count': 1, 'right_count': 1, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'L1', 'total_count': 1776, 'left_count': 884, 'right_count': 892, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 880, 'coverage': 3.853409090909091, 'cell_size': 4.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 892, 'coverage': 3.874439461883408, 'cell_size': 4.0}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 886.0, 'coverage': 3.86392427639625, 'cell_size': 4.0}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'MeVP14', 'total_count': 33, 'left_count': 16, 'right_count': 17, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 363, 'coverage': 3.0137741046831956, 'cell_size': 70.0}, 'LO': {'cols_innervated': 91, 'coverage': 3.32967032967033, 'cell_size': 18.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 404, 'coverage': 3.2747524752475248, 'cell_size': 80.0}, 'LO': {'cols_innervated': 106, 'coverage': 3.5377358490566038, 'cell_size': 18.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 383.5, 'coverage': 3.14426328996536, 'cell_size': 75.0}, 'LO': {'cols_innervated': 98.5, 'coverage': 3.433703089363467, 'cell_size': 18.0}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'MeVPMe2', 'total_count': 10, 'left_count': 5, 'right_count': 5, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 851, 'coverage': 5.048178613396004, 'cell_size': 419.5}, 'LO': {'cols_innervated': 47, 'coverage': 1.0, 'cell_size': 1.0}, 'LOP': {'cols_innervated': 44, 'coverage': 1.0227272727272727, 'cell_size': 7.0}}, 'R': {'ME': {'cols_innervated': 873, 'coverage': 5.128293241695304, 'cell_size': 438.5}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 32, 'coverage': 1.21875, 'cell_size': 19.5}}, 'both': {'ME': {'cols_innervated': 862.0, 'coverage': 5.088235927545654, 'cell_size': 429.0}, 'LO': {'cols_innervated': 23.5, 'coverage': 1.0, 'cell_size': 1.0}, 'LOP': {'cols_innervated': 38.0, 'coverage': 1.1207386363636362, 'cell_size': 13.25}}}}, {'name': 'Pm5', 'total_count': 182, 'left_count': 88, 'right_count': 94, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 877, 'coverage': 4.866590649942988, 'cell_size': 48.0}, 'LO': {'cols_innervated': 6, 'coverage': 1.0, 'cell_size': 1.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 892, 'coverage': 5.0459641255605385, 'cell_size': 47.5}, 'LO': {'cols_innervated': 3, 'coverage': 1.0, 'cell_size': 1.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 884.5, 'coverage': 4.956277387751763, 'cell_size': 47.75}, 'LO': {'cols_innervated': 4.5, 'coverage': 1.0, 'cell_size': 1.0}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'SLP018', 'total_count': 10, 'left_count': 5, 'right_count': 5, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'SNpp10', 'total_count': 7, 'left_count': 0, 'right_count': 0, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LO': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'Tm35', 'total_count': 86, 'left_count': 43, 'right_count': 43, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 507, 'coverage': 2.035502958579882, 'cell_size': 24.0}, 'LO': {'cols_innervated': 560, 'coverage': 2.244642857142857, 'cell_size': 29.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'R': {'ME': {'cols_innervated': 560, 'coverage': 2.0892857142857144, 'cell_size': 27.0}, 'LO': {'cols_innervated': 561, 'coverage': 2.1853832442067738, 'cell_size': 28.0}, 'LOP': {'cols_innervated': 0, 'coverage': None, 'cell_size': None}}, 'both': {'ME': {'cols_innervated': 533.5, 'coverage': 2.0623943364327983, 'cell_size': 25.5}, 'LO': {'cols_innervated': 560.5, 'coverage': 2.2150130506748154, 'cell_size': 28.5}, 'LOP': {'cols_innervated': 0.0, 'coverage': None, 'cell_size': None}}}}, {'name': 'TmY13', 'total_count': 432, 'left_count': 221, 'right_count': 211, 'middle_count': 0, 'undefined_count': 0, 'has_undefined': False, 'spatial_metrics': {'L': {'ME': {'cols_innervated': 875, 'coverage': 4.619428571428571, 'cell_size': 18.0}, 'LO': {'cols_innervated': 855, 'coverage': 2.2432748538011698, 'cell_size': 9.0}, 'LOP': {'cols_innervated': 654, 'coverage': 1.607033639143731, 'cell_size': 5.0}}, 'R': {'ME': {'cols_innervated': 891, 'coverage': 4.721661054994389, 'cell_size': 20.0}, 'LO': {'cols_innervated': 850, 'coverage': 2.2411764705882353, 'cell_size': 9.0}, 'LOP': {'cols_innervated': 713, 'coverage': 1.817671809256662, 'cell_size': 7.0}}, 'both': {'ME': {'cols_innervated': 883.0, 'coverage': 4.67054481321148, 'cell_size': 19.0}, 'LO': {'cols_innervated': 852.5, 'coverage': 2.2422256621947025, 'cell_size': 9.0}, 'LOP': {'cols_innervated': 683.5, 'coverage': 1.7123527242001964, 'cell_size': 6.0}}}}]

def extract_points(records, side, region):
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
        if x is None or y is None: 
            continue
        try: y = float(y)
        except: continue
        pts.append({"name": name, "x": int(x), "y": y})
    return pts

def nice_ticks(vmin, vmax, n=5):
    """Very small 'nice' tick helper for axes."""
    if vmin == vmax:
        return [vmin]
    span = vmax - vmin
    raw = span / max(1, (n - 1))
    # round raw to 1/2/5 * 10^k
    pow10 = 10 ** floor(len(str(int(raw))) - 1 if raw >= 1 else 0)
    base = raw / pow10
    if base <= 1: step = 1
    elif base <= 2: step = 2
    elif base <= 5: step = 5
    else: step = 10
    step *= pow10
    start = floor(vmin / step) * step
    end = ceil(vmax / step) * step
    ticks = []
    v = start
    # cap to avoid runaway in pathological cases
    for _ in range(1000):
        ticks.append(v)
        v += step
        if v > end + 1e-9:
            break
    return ticks

def scale(v, vmin, vmax, a, b):
    if vmax == vmin:
        return (a + b) / 2.0
    return a + (v - vmin) * (b - a) / (vmax - vmin)

def prepare(points, width=680, height=420, margins=(50, 20, 30, 50)):
    """Compute pixel positions for an SVG scatter plot."""
    top, right, bottom, left = margins
    plot_w = width - left - right
    plot_h = height - top - bottom

    xmin = min(p["x"] for p in points)
    xmax = max(p["x"] for p in points)
    ymin = min(p["y"] for p in points)
    ymax = max(p["y"] for p in points)

    # expand bounds a little so dots don't sit on the frame
    pad_x = 0.05 * (xmax - xmin or 1)
    pad_y = 0.08 * (ymax - ymin or 1)
    xmin -= pad_x; xmax += pad_x
    ymin -= pad_y; ymax += pad_y

    # ticks
    xticks = nice_ticks(xmin, xmax, n=6)
    yticks = nice_ticks(ymin, ymax, n=6)

    # scale points to pixels (y inverted for SVG)
    for p in points:
        p["sx"] = scale(p["x"], xmin, xmax, 0, plot_w)
        p["sy"] = scale(p["y"], ymin, ymax, plot_h, 0)
        p["r"] = 4
        p["tooltip"] = f"{p['name']}\ncount: {p['x']}\nL→ME cell_size: {p['y']:.3f}"

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
        "points": points,
        "title": "L → ME: total_count vs cell_size",
        "subtitle": "one marker per name",
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
    .plot-bg { fill:#ffffff; stroke:#dddddd; }
    .axis-line { stroke:#888; stroke-width:1; shape-rendering:crispEdges; }
    .tick { stroke:#bbb; stroke-width:1; shape-rendering:crispEdges; }
    .tick-label { fill:#444; font-size:10px; font-family:Helvetica, Arial, sans-serif; }
    .title { fill:#666; font-size:12px; font-family:Arial, sans-serif; }
    .subtitle { fill:#999; font-size:10px; font-family:Arial, sans-serif; }
    .dot { cursor:pointer; opacity:0.85; transition:opacity 0.15s; }
    .dot:hover { opacity:1; }
    .tooltip-box { pointer-events:none; transition:opacity 0.15s; }
    .tooltip-bg { fill:rgba(0,0,0,0.8); rx:3; ry:3; }
    .tooltip-text { fill:#fff; font-size:12px; font-family:Helvetica, Arial, sans-serif; }
  </style>
</defs>

<script type="text/ecmascript">
//<![CDATA[
function showTip(evt) {
  const svg = evt.currentTarget.ownerSVGElement;
  const tip = svg.getElementById("tooltip");
  const g = evt.currentTarget;           // <g class="marker">
  const c = g.querySelector("circle");

  // enlarge circle
  const base = parseFloat(c.getAttribute("data-base-r") || "4");
  c.setAttribute("r", String(base * 1.8));

  // compute tooltip text from data-title
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
  const boxW = Math.max(maxW + pad * 2, 120);
  const boxH = lines.length * lh + pad * 2;
  rect.setAttribute("width", boxW);
  rect.setAttribute("height", boxH);

  // position near mouse, clamp to viewport
  const bounds = svg.getBoundingClientRect();
  let x = evt.clientX - bounds.left + 10;
  let y = evt.clientY - bounds.top  - boxH - 10;
  if (x + boxW > {{ width }}) x = {{ width }} - boxW - 5;
  if (y < 0) y = evt.clientY - bounds.top + 10;
  if (x < 0) x = 5;

  tip.setAttribute("transform", "translate(" + x + "," + y + ")");
  tip.setAttribute("opacity", "1");

  // suppress native <title> popups
  const tEl = g.querySelector("title");
  if (tEl) tEl.textContent = "";
}

function hideTip(evt) {
  const svg = evt.currentTarget.ownerSVGElement;
  const tip = svg.getElementById("tooltip");
  tip.setAttribute("opacity", "0");

  // restore radius
  const g = evt.currentTarget;
  const c = g.querySelector("circle");
  const base = parseFloat(c.getAttribute("data-base-r") || "4");
  c.setAttribute("r", String(base));

  // restore native title text for accessibility
  const text = c.getAttribute("data-title") || "";
  const tEl = g.querySelector("title");
  if (tEl) tEl.textContent = text;
}
//]]>
</script>

<!-- Titles -->
<text x="8" y="16" class="title">{{ title }}</text>
<text x="8" y="30" class="subtitle">{{ subtitle }}</text>

<!-- Plot area -->
<g id="scatter"
   transform="translate({{ margin_left }}, {{ margin_top }})">
  <rect class="plot-bg" x="0" y="0" width="{{ plot_w }}" height="{{ plot_h }}" />

  <!-- grid + ticks (X) -->
  {% for t in xticks %}
  {% set px = (t - xmin) / (xmax - xmin) * plot_w if xmax != xmin else plot_w/2 %}
  <line class="tick" x1="{{ px }}" y1="0" x2="{{ px }}" y2="{{ plot_h }}" />
  <text class="tick-label" x="{{ px }}" y="{{ plot_h + 14 }}" text-anchor="middle">{{ '{:.0f}'.format(t) }}</text>
  {% endfor %}
  <line class="axis-line" x1="0" y1="{{ plot_h }}" x2="{{ plot_w }}" y2="{{ plot_h }}" />

  <!-- grid + ticks (Y) -->
  {% for t in yticks %}
  {% set py = plot_h - (t - ymin) / (ymax - ymin) * plot_h if ymax != ymin else plot_h/2 %}
  <line class="tick" x1="0" y1="{{ py }}" x2="{{ plot_w }}" y2="{{ py }}" />
  <text class="tick-label" x="-6" y="{{ py + 3 }}" text-anchor="end">{{ '{:.2f}'.format(t) }}</text>
  {% endfor %}
  <line class="axis-line" x1="0" y1="0" x2="0" y2="{{ plot_h }}" />

  <!-- markers -->
  {% for p in points %}
  <g class="marker" transform="translate({{ p.sx }}, {{ p.sy }})" onmouseover="showTip(event)" onmouseout="hideTip(event)">
    <circle r="{{ p.r }}" data-base-r="{{ p.r }}" class="dot" data-title="{{ p.tooltip | e }}" fill="#4682b4">
      <title>{{ p.tooltip }}</title>
    </circle>
  </g>
  {% endfor %}
</g>

<!-- tooltip (top layer) -->
<g id="tooltip" class="tooltip-box" opacity="0">
  <rect id="tooltip-bg" class="tooltip-bg" width="120" height="40" />
  <g id="tooltip-text-group"></g>
</g>
</svg>
""")

if __name__ == "__main__":
    side = "R"
    region = "ME"
    points = extract_points(plot_data, side=side, region=region)
    print(points)
    if not points:
        raise SystemExit("No points found: ensure R→ME cell_size values exist.")
    ctx = prepare(points)
    svg = SVG_TEMPLATE.render(**ctx)
    with open(f"scatter_{side}_{region}.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote scatter_{side}_{region}.svg")
