"""Renders selector.py's chart specs as Observable Plot embeds — spec §15
names Plot as the primary renderer. No server-side chart rendering: each
chart is a small self-contained ES module that mounts into a placeholder
div, sized to its container at runtime (spec §13 — not just a shrunk
desktop chart, it's genuinely responsive). Every chart also ships a plain
HTML data table fallback (spec §14 accessibility — works with JS off).
"""
import json

from config import ACCENT_COLOUR

MUTED = "#6B6B63"
RULE = "#E4E2DA"
PLOT_CDN = "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"


def render_all(chart_specs: list[dict]) -> list[str]:
    return [_render_one(spec, i) for i, spec in enumerate(chart_specs)]


def _render_one(spec: dict, index: int) -> str:
    container_id = f"chart-{index}"
    builder = _BUILDERS.get(spec["chart_type"])
    if builder is None:
        return ""
    js = builder(spec, container_id)
    fallback = _fallback_table(spec)
    return f"""
<figure class="chart-block">
  <figcaption class="chart-title">{_esc(spec['title'])}</figcaption>
  <div id="{container_id}" class="obs-plot-container" role="img" aria-label="{_esc(spec['title'])}"></div>
  <details class="chart-data"><summary>View underlying data</summary>{fallback}</details>
</figure>
<script type="module">
import * as Plot from "{PLOT_CDN}";
{js}
</script>
"""


def _fallback_table(spec: dict) -> str:
    data = spec["data"]
    if spec["chart_type"] == "line_annotated":
        rows = zip(data["periods"], data["values"])
        head = ("Period", spec.get("value_field", "Value"))
    elif spec["chart_type"] == "lollipop":
        rows = zip(data["labels"], data["values"])
        head = ("Category", "Value")
    elif spec["chart_type"] == "scatter":
        rows = zip(data["x"], data["y"])
        head = (spec.get("x_field", "X"), spec.get("y_field", "Y"))
    else:  # histogram
        vals = sorted(data["values"])
        rows = [("min", round(vals[0], 3)), ("median", round(vals[len(vals) // 2], 3)), ("max", round(vals[-1], 3)),
                ("count", len(vals))]
        head = ("Statistic", "Value")

    body = "".join(f"<tr><td>{_esc(a)}</td><td class='tabular-nums'>{_esc(b)}</td></tr>" for a, b in rows)
    return f"<table><thead><tr><th>{_esc(head[0])}</th><th>{_esc(head[1])}</th></tr></thead><tbody>{body}</tbody></table>"


def _esc(v) -> str:
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_line_annotated(spec: dict, container_id: str) -> str:
    data = [{"period": p, "value": v} for p, v in zip(spec["data"]["periods"], spec["data"]["values"]) if v is not None]
    ann_i = min(spec.get("annotation_index", len(data) - 1), len(data) - 1)
    return f"""
const data = {json.dumps(data)};
const annIndex = {ann_i};
const container = document.getElementById("{container_id}");
const width = Math.min(820, container.clientWidth || 680);
const plot = Plot.plot({{
  width, height: 320, marginLeft: 56, marginBottom: 40,
  x: {{label: null, type: "point"}}, y: {{label: "{_esc(spec.get('value_field', 'value'))}", grid: true}},
  marks: [
    Plot.lineY(data, {{x: "period", y: "value", stroke: "{ACCENT_COLOUR}", strokeWidth: 2.2}}),
    Plot.dot(data, {{x: "period", y: "value", r: (d, i) => i === annIndex ? 5 : 2.5,
                     fill: (d, i) => i === annIndex ? "{ACCENT_COLOUR}" : "{MUTED}"}}),
    Plot.text(data.filter((d, i) => i === annIndex), {{x: "period", y: "value", text: d => d.value,
               dy: -14, fontWeight: 600, fill: "{ACCENT_COLOUR}"}}),
    Plot.tip(data, Plot.pointerX({{x: "period", y: "value", title: d => `${{d.period}}: ${{d.value}}`}})),
  ],
}});
container.append(plot);
"""


def _build_lollipop(spec: dict, container_id: str) -> str:
    data = [{"label": str(l)[:40], "value": v} for l, v in zip(spec["data"]["labels"], spec["data"]["values"])]
    return f"""
const data = {json.dumps(data)};
const container = document.getElementById("{container_id}");
const width = Math.min(820, container.clientWidth || 680);
const plot = Plot.plot({{
  width, height: Math.max(120, data.length * 34), marginLeft: 200,
  x: {{label: "value", grid: true}}, y: {{label: null}},
  marks: [
    Plot.ruleY(data, {{y: "label", x1: 0, x2: "value", stroke: "{RULE}", strokeWidth: 2}}),
    Plot.dot(data, {{y: "label", x: "value", r: 5, fill: "{ACCENT_COLOUR}"}}),
    Plot.text(data, {{y: "label", x: "value", text: d => d.value, dx: 18, fill: "#1A1A18"}}),
    Plot.tip(data, Plot.pointer({{y: "label", x: "value", title: d => `${{d.label}}: ${{d.value}}`}})),
  ],
}});
container.append(plot);
"""


def _build_scatter(spec: dict, container_id: str) -> str:
    data = [{"x": x, "y": y} for x, y in zip(spec["data"]["x"], spec["data"]["y"])]
    return f"""
const data = {json.dumps(data)};
const container = document.getElementById("{container_id}");
const width = Math.min(820, container.clientWidth || 680);
const plot = Plot.plot({{
  width, height: 380, marginLeft: 56,
  x: {{label: "{_esc(spec.get('x_field', 'x'))}", grid: true}},
  y: {{label: "{_esc(spec.get('y_field', 'y'))}", grid: true}},
  marks: [
    Plot.dot(data, {{x: "x", y: "y", r: 3.5, fill: "{ACCENT_COLOUR}", fillOpacity: 0.55}}),
    Plot.linearRegressionY(data, {{x: "x", y: "y", stroke: "{MUTED}", strokeDasharray: "3,3"}}),
    Plot.tip(data, Plot.pointer({{x: "x", y: "y", title: d => `(${{d.x}}, ${{d.y}})`}})),
  ],
}});
container.append(plot);
"""


def _build_histogram(spec: dict, container_id: str) -> str:
    values = spec["data"]["values"]
    return f"""
const data = {json.dumps(values)};
const container = document.getElementById("{container_id}");
const width = Math.min(820, container.clientWidth || 680);
const plot = Plot.plot({{
  width, height: 320, marginLeft: 56,
  x: {{label: "{_esc(spec.get('field', 'value'))}"}}, y: {{label: "count", grid: true}},
  marks: [
    Plot.rectY(data, Plot.binX({{y: "count"}}, {{x: d => d, fill: "{ACCENT_COLOUR}", fillOpacity: 0.85}})),
    Plot.ruleY([0]),
  ],
}});
container.append(plot);
"""


_BUILDERS = {
    "line_annotated": _build_line_annotated,
    "lollipop": _build_lollipop,
    "scatter": _build_scatter,
    "histogram": _build_histogram,
}
