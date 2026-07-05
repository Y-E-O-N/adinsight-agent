from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

DEFAULT_METRICS_PATH = Path("metrics/run_results.jsonl")
DEFAULT_OUTPUT_PATH = Path("docs/images/06_text2sql_eval_summary.svg")
TEXT2SQL_EVAL_STEPS = {
    "text2sql_v2_mock_eval",
    "text2sql_v2_eval",
    "text2sql_negative_eval",
}


def main() -> None:
    records = load_text2sql_eval_records(DEFAULT_METRICS_PATH)
    svg = render_svg(records[-8:])
    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"wrote {DEFAULT_OUTPUT_PATH} records={len(records[-8:])}")


def load_text2sql_eval_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("step") in TEXT2SQL_EVAL_STEPS:
            records.append(payload)
    return records


def render_svg(records: list[dict[str, Any]]) -> str:
    width = 980
    height = 520
    margin_left = 72
    margin_right = 32
    margin_top = 72
    margin_bottom = 96
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    max_total = max((int(record.get("total", 0) or 0) for record in records), default=1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="title desc">',
        "<title>Text2SQL Eval Summary</title>",
        "<desc>Stacked bar chart of recent Text2SQL positive and negative eval runs.</desc>",
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
        '<text x="40" y="38" font-family="Arial, sans-serif" font-size="22" '
        'font-weight="700" fill="#111827">Text2SQL Eval Summary</text>',
        '<text x="40" y="60" font-family="Arial, sans-serif" font-size="13" '
        'fill="#4b5563">Recent positive and negative eval records from metrics/run_results.jsonl</text>',
        render_axes(margin_left, margin_top, plot_width, plot_height, max_total),
        render_legend(width - 390, 28),
    ]

    if not records:
        parts.append(
            '<text x="72" y="240" font-family="Arial, sans-serif" font-size="16" '
            'fill="#6b7280">No Text2SQL eval records found.</text>'
        )
    else:
        parts.extend(
            render_bars(
                records,
                margin_left,
                margin_top,
                plot_width,
                plot_height,
                max_total,
            )
        )

    parts.append("</svg>")
    return "\n".join(parts)


def render_axes(
    margin_left: int,
    margin_top: int,
    plot_width: int,
    plot_height: int,
    max_total: int,
) -> str:
    y_bottom = margin_top + plot_height
    grid_lines = []
    for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = y_bottom - plot_height * ratio
        value = round(max_total * ratio)
        grid_lines.append(
            f'<line x1="{margin_left}" y1="{y:.1f}" x2="{margin_left + plot_width}" '
            'y2="{:.1f}" stroke="#e5e7eb"/>'.format(y)
        )
        grid_lines.append(
            f'<text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" '
            'font-family="Arial, sans-serif" font-size="11" fill="#6b7280">'
            f"{value}</text>"
        )

    grid_lines.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" '
        f'y2="{y_bottom}" stroke="#9ca3af"/>'
    )
    grid_lines.append(
        f'<line x1="{margin_left}" y1="{y_bottom}" '
        f'x2="{margin_left + plot_width}" y2="{y_bottom}" stroke="#9ca3af"/>'
    )
    return "\n".join(grid_lines)


def render_legend(x: int, y: int) -> str:
    items = [
        ("passed", "#16a34a"),
        ("refused", "#f59e0b"),
        ("blocked", "#ef4444"),
        ("failed", "#7c3aed"),
    ]
    parts = []
    for index, (label, color) in enumerate(items):
        item_x = x + index * 92
        parts.append(f'<rect x="{item_x}" y="{y}" width="12" height="12" fill="{color}"/>')
        parts.append(
            f'<text x="{item_x + 18}" y="{y + 11}" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#374151">{label}</text>'
        )
    return "\n".join(parts)


def render_bars(
    records: list[dict[str, Any]],
    margin_left: int,
    margin_top: int,
    plot_width: int,
    plot_height: int,
    max_total: int,
) -> list[str]:
    colors = {
        "passed": "#16a34a",
        "refused": "#f59e0b",
        "blocked": "#ef4444",
        "failed": "#7c3aed",
    }
    y_bottom = margin_top + plot_height
    slot_width = plot_width / max(len(records), 1)
    bar_width = min(64, slot_width * 0.56)
    parts: list[str] = []

    for index, record in enumerate(records):
        x = margin_left + slot_width * index + (slot_width - bar_width) / 2
        y_cursor = y_bottom
        values = segment_values(record)

        for key in ("passed", "refused", "blocked", "failed"):
            value = values[key]
            if value <= 0:
                continue
            segment_height = plot_height * (value / max_total)
            y_cursor -= segment_height
            parts.append(
                f'<rect x="{x:.1f}" y="{y_cursor:.1f}" width="{bar_width:.1f}" '
                f'height="{segment_height:.1f}" fill="{colors[key]}">'
                f"<title>{key}: {value}</title></rect>"
            )

        parts.extend(render_bar_label(record, x + bar_width / 2, y_bottom + 18))

    return parts


def segment_values(record: dict[str, Any]) -> dict[str, int]:
    if record.get("step") == "text2sql_negative_eval":
        return {
            "passed": 0,
            "refused": int(record.get("refused", 0) or 0),
            "blocked": int(record.get("blocked", 0) or 0),
            "failed": int(record.get("failed", 0) or 0),
        }

    return {
        "passed": int(record.get("passed", 0) or 0),
        "refused": int(record.get("refused", 0) or 0),
        "blocked": int(record.get("blocked", 0) or 0),
        "failed": int(record.get("failed", 0) or 0),
    }


def render_bar_label(record: dict[str, Any], x_center: float, y: float) -> list[str]:
    step = str(record.get("step", "eval")).replace("text2sql_", "").replace("_eval", "")
    mode = str(record.get("mode", "")).replace("llm_generated_sql_", "")
    score = record.get("model_score", {}).get("composite_score")
    rate = record.get("negative_pass_rate")
    metric = f"score {score}" if score is not None else f"neg {rate}" if rate is not None else ""
    label_1 = html.escape(step)
    label_2 = html.escape(metric or mode)

    return [
        f'<text x="{x_center:.1f}" y="{y:.1f}" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="11" fill="#374151">'
        f"{label_1}</text>",
        f'<text x="{x_center:.1f}" y="{y + 15:.1f}" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="10" fill="#6b7280">'
        f"{label_2}</text>",
    ]


if __name__ == "__main__":
    main()
