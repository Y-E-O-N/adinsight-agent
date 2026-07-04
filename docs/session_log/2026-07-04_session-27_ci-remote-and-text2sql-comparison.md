# Session 27 — CI Remote Pass and Text2SQL Eval Comparison (2026-07-04)

**Phase**: Phase 8C + Phase 5C
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- GitHub Actions 첫 원격 실행 상태를 확인한다.
- Text2SQL v1/v2 평가 결과를 포트폴리오 표로 정리한다.
- v2 mock의 refusal/failure 의미를 면접에서 설명 가능하게 만든다.

## Done
- [x] `gh run list --limit 3`로 GitHub Actions 첫 실행을 확인했다.
  - run id: `28706620035`
  - status: `completed`
  - conclusion: `success`
  - commit: `fcc8afa Add Python CI workflow`
- [x] Text2SQL v1/v2 comparison 문서를 추가했다.
  - `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md`
- [x] README/portfolio/CLAUDE/session index/metrics를 갱신했다.

## Decisions
- **v2 mock refusal은 실패로 과장하지 않는다**: mock provider가 아직 2개 질문만 지원하므로 16 REFUSED는 안전한 거절로 해석한다.
- **v1 baseline을 계속 유지한다**: v1 `18 PASS`는 실사용 가능한 deterministic baseline이고, v2는 provider 확장 전 regression target이다.

## Files changed
- `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/2026-07-04_session-27_ci-remote-and-text2sql-comparison.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Concepts taught
- **Refusal rate** — 답변하지 않는 비율이다. LLM SQL에서는 틀린 SQL을 실행하는 것보다 안전하게 거절하는 것이 더 나을 수 있다.
- **Answerable-only Exec Acc** — 답변을 시도한 케이스 중 맞춘 비율이다. 전체 coverage와 함께 봐야 한다.

## Portfolio assets added
- GitHub Actions remote success evidence:
  - run id `28706620035`
- Text2SQL v1/v2 eval comparison:
  - `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md`

## Metrics
- CI remote run: success
- v1 eval: `18 PASS / 0 FAIL`
- v2 mock eval: `2 PASS / 16 REFUSED / 0 BLOCKED`

## Next session — start here
1. Decide whether to expand v2 mock coverage or connect a real provider.
2. Recommended next step:
   - add more mock SQL generations for `p5_q002`, `p5_q005`, `p5_q007`
   - then rerun `agent/eval/run_text2sql_v2_eval.py`
