from __future__ import annotations

from agent.eval.render_text2sql_eval_chart import render_svg, segment_values


def test_render_svg_includes_eval_segments() -> None:
    svg = render_svg(
        [
            {
                "step": "text2sql_v2_eval",
                "mode": "llm_generated_sql_v2_mock",
                "total": 24,
                "passed": 13,
                "refused": 11,
                "blocked": 0,
                "failed": 0,
                "model_score": {"composite_score": 73.5},
            }
        ]
    )

    assert "<svg" in svg
    assert "Text2SQL Eval Summary" in svg
    assert "score 73.5" in svg
    assert "passed: 13" in svg


def test_segment_values_does_not_double_count_negative_passes() -> None:
    values = segment_values(
        {
            "step": "text2sql_negative_eval",
            "total": 8,
            "passed": 8,
            "refused": 8,
            "blocked": 0,
            "failed": 0,
        }
    )

    assert values == {
        "passed": 0,
        "refused": 8,
        "blocked": 0,
        "failed": 0,
    }
