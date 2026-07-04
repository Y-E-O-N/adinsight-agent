# Session 22 — Text2SQL Demo GIF Capture (2026-06-29)

**Phase**: Phase 6/7 — Text2SQL demo evidence asset
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- Session 21 runbook을 실제 포트폴리오 증거물로 바꾼다.
- `/query` 영어/한국어 smoke를 현재 데이터 기준으로 다시 실행한다.
- Text2SQL demo GIF와 evidence 문서를 남긴다.

## Done
- [x] Docker Compose 상태를 확인했다.
  - Postgres, Superset, Airflow services are healthy/running.
  - FastAPI는 실행 중이 아니어서 `uvicorn api.main:app`로 로컬 기동했다.
- [x] `/health` smoke를 확인했다.
  - `{"status":"ok","service":"adinsight-api"}`
- [x] English `/query` smoke를 재실행했다.
  - question: `"Which campaigns have the highest ROAS?"`
  - `question_id`: `p5_q001`
  - rows: `5`
  - top campaign: `camp_000029`
  - latency: `44.922ms`
- [x] Korean `/query` smoke를 재실행했다.
  - question: `"최신 ROAS 예측 모델의 MAE와 bias를 요약해줘."`
  - `question_id`: `p5_q008`
  - rows: `1`
  - MAE: `0.07988873820803322`
  - latency: `41.072ms`
- [x] evidence 문서를 추가했다.
  - `docs/analysis/stage6_text2sql_demo_evidence.md`
- [x] demo GIF 생성 스크립트를 추가했다.
  - `dashboards/scripts/create_text2sql_demo_gif.sh`
- [x] demo GIF를 생성하고 시각 확인했다.
  - `docs/images/06_text2sql_demo.gif`
  - size: `111KB`
  - dimensions: `960x540`

## Decisions
- **외부 이미지 dependency를 추가하지 않는다**: `Pillow`, `matplotlib`, `imageio`가 설치되어 있지 않았고, 이 산출물 하나 때문에 dependency를 늘리지 않았다.
- **ASCII terminal-style GIF로 만든다**: 현재 `ffmpeg` 빌드에 `drawtext`/subtitle filter가 없어, Python 표준 라이브러리로 PPM frame을 생성하고 `ffmpeg`로 GIF만 인코딩했다.
- **한국어 원문은 evidence 문서에 남긴다**: GIF는 ASCII summary 중심이고, 한국어 질문 원문과 SQL은 `docs/analysis/stage6_text2sql_demo_evidence.md`에 보존한다.

## Files changed
- `dashboards/scripts/create_text2sql_demo_gif.sh` — dependency-free GIF generator
- `docs/images/06_text2sql_demo.gif` — Text2SQL demo GIF
- `docs/analysis/stage6_text2sql_demo_evidence.md` — current `/query` smoke evidence
- `docs/analysis/stage6_text2sql_superset_demo_runbook.md` — artifact link update
- `README.md` — demo GIF/evidence link
- `docs/portfolio_draft.md` — Text2SQL demo GIF checklist marked done
- `metrics/run_results.jsonl` — demo capture metric append

## Concepts taught
- **Evidence artifact** — 실측 결과는 채팅에만 두지 않고, 재사용 가능한 문서/이미지/metrics로 남긴다.
- **Dependency discipline** — 포트폴리오 자산 하나를 위해 런타임 dependency를 늘리기보다, 표준 도구로 재현 가능한 생성 경로를 둔다.

## Portfolio assets added
- `docs/images/06_text2sql_demo.gif`
- `docs/analysis/stage6_text2sql_demo_evidence.md`
- `dashboards/scripts/create_text2sql_demo_gif.sh`

## Open questions
- 이 문서/이미지 변경과 scheduled daily metric 3줄을 함께 커밋할지 결정한다.
- 다음 구현은 AWS target architecture 문서 또는 LLM SQL generation v2 중 하나가 자연스럽다.

## Metrics
- `/query` English latency: `44.922ms`
- `/query` Korean latency: `41.072ms`
- GIF: `960x540`, `111KB`

## Next session — start here
1. Check dirty state:
   ```bash
   git status --short --branch
   git diff --stat
   ```
2. If committing, include the demo docs/GIF and decide whether to include the scheduled `metrics/run_results.jsonl` daily rows.
3. Recommended next task:
   - AWS target architecture document for `/query` + `/predict`
   - or LLM SQL generation v2 design guarded by the existing expected-SQL evaluator
