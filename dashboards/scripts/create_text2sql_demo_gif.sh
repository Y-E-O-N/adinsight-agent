#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="${TMPDIR:-/tmp}/adinsight_text2sql_demo_gif"
OUTPUT="$ROOT_DIR/docs/images/06_text2sql_demo.gif"

mkdir -p "$TMP_DIR"

python3 - "$TMP_DIR" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

out_dir = Path(sys.argv[1])
width, height = 1280, 720

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["00111", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "11100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "01100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "'": ["01100", "01100", "01000", "00000", "00000", "00000", "00000"],
    '"': ["01010", "01010", "01010", "00000", "00000", "00000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}

COLORS = {
    "bg": (16, 24, 32),
    "panel": (23, 33, 43),
    "green": (52, 211, 153),
    "white": (248, 250, 252),
    "muted": (148, 163, 184),
    "yellow": (250, 204, 21),
}

def fill(img: bytearray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    for y in range(y0, y1):
        row = y * width * 3
        for x in range(x0, x1):
            idx = row + x * 3
            img[idx:idx + 3] = bytes(color)

def text(img: bytearray, x: int, y: int, value: str, scale: int, color: tuple[int, int, int]) -> None:
    cursor = x
    for ch in value.upper():
        glyph = FONT.get(ch, FONT["?"])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    fill(
                        img,
                        cursor + gx * scale,
                        y + gy * scale,
                        cursor + (gx + 1) * scale,
                        y + (gy + 1) * scale,
                        color,
                    )
        cursor += 6 * scale

def frame(lines: list[tuple[str, int, tuple[int, int, int]]], name: str) -> None:
    img = bytearray(COLORS["bg"] * (width * height))
    fill(img, 36, 36, width - 36, height - 36, COLORS["panel"])
    fill(img, 36, 36, width - 36, 42, COLORS["green"])
    y = 76
    for line, scale, color in lines:
        text(img, 76, y, line, scale, color)
        y += 8 * scale + 22
    path = out_dir / name
    with path.open("wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        f.write(img)

frames = [
    [
        ("1. SUPERSET MONITOR", 7, COLORS["green"]),
        ("ADINSIGHT CAMPAIGN ROAS PREDICTION", 5, COLORS["white"]),
        ("CHECK LATEST PREDICTION ERRORS FIRST", 4, COLORS["muted"]),
        ("DASHBOARD: ADINSIGHT CAMPAIGN ROAS", 4, COLORS["white"]),
    ],
    [
        ("2. ENGLISH QUERY -> /QUERY", 7, COLORS["green"]),
        ("WHICH CAMPAIGNS HAVE THE HIGHEST ROAS?", 4, COLORS["white"]),
        ("QUESTION_ID: P5_Q001", 4, COLORS["yellow"]),
        ("MODEL: AI_NATIVE.AI_CAMPAIGN_ROI_SUMMARY", 4, COLORS["white"]),
        ("ROWS: 5  TOP: CAMP_000029  LATENCY: 44.922MS", 4, COLORS["white"]),
    ],
    [
        ("3. KOREAN MAE/BIAS", 7, COLORS["green"]),
        ("QUESTION_ID: P5_Q008", 4, COLORS["yellow"]),
        ("MODEL: MARTS.MART_CAMPAIGN_ROAS_PREDICTION_MONITOR", 4, COLORS["white"]),
        ("ROWS: 1  MAE: 0.07988873820803322", 4, COLORS["white"]),
        ("BIAS: -1.095444E-16  LATENCY: 41.072MS", 4, COLORS["white"]),
    ],
    [
        ("4. GENERATED SQL V2", 7, COLORS["green"]),
        ("MODE: LLM_GENERATED_SQL_V2_HTTP_JSON", 4, COLORS["white"]),
        ("FINAL_PROVIDER: GEMINI", 4, COLORS["yellow"]),
        ("COST: $0.0014719  PROVIDER: 4672.489MS", 4, COLORS["white"]),
        ("CACHED_INPUT_RATIO: 0.8229", 4, COLORS["white"]),
    ],
    [
        ("5. DUAL PROVIDER FALLBACK", 7, COLORS["green"]),
        ("SAFETY REFUSAL: GEMINI -> OPENAI", 4, COLORS["white"]),
        ("FINAL_PROVIDER: OPENAI  HTTP: 404", 4, COLORS["yellow"]),
        ("FALLBACK_REASON: PRIMARY_CONTENT_SAFETY_REFUSAL", 4, COLORS["white"]),
        ("COST: $0.0067335  PROVIDER: 6989.124MS", 4, COLORS["white"]),
    ],
    [
        ("6. OPENAI VS GEMINI", 7, COLORS["green"]),
        ("SAME SCOPE: 24 POSITIVE AND 14 NEGATIVE", 4, COLORS["white"]),
        ("OPENAI: 38/38 PASS  COST: $0.103027", 4, COLORS["yellow"]),
        ("GEMINI: 36/38 PASS  COST: $0.064098", 4, COLORS["yellow"]),
        ("GEMINI 37.8% CHEAPER  OPENAI 16.5% FASTER", 4, COLORS["white"]),
    ],
    [
        ("7. GUARDRAILS", 7, COLORS["green"]),
        ("MODE: DETERMINISTIC_EXPECTED_SQL_REGISTRY_V1", 4, COLORS["white"]),
        ("V2: VALIDATED SQL ONLY", 4, COLORS["white"]),
        ("AUDIT: PROVIDER COST LATENCY CACHE RATIO", 4, COLORS["white"]),
        ("FALLBACK STATUS IS RECORDED PER REQUEST", 4, COLORS["muted"]),
    ],
]

for idx, lines in enumerate(frames, start=1):
    frame(lines, f"frame{idx:02d}.ppm")
PY

ffmpeg -y \
  -framerate 0.5 -i "$TMP_DIR/frame%02d.ppm" \
  -vf "fps=8,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  "$OUTPUT" >/dev/null 2>&1

echo "$OUTPUT"
