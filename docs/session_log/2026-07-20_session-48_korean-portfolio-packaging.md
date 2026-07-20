# Session 48 — Korean Portfolio Packaging (2026-07-20)

**Phase**: Phase 9B — 문서화 + 한국 기업 제출 패키지
**Duration**: ~90m
**Operator**: Yeon (with Codex)

## Goals

- 지금까지의 AdInsight 진행 내용을 데이터 엔지니어 취업용 포트폴리오로 재구성한다.
- 한국 기업 제출 기준에 맞춰 README, PDF/DOCX 후보 문서, 이력서 bullet, 지원서 입력 문구, 면접 복습 자료를 만든다.
- 과장된 claim과 미구현 항목을 분리해 공개 가능한 주장만 남긴다.

## Done

- [x] `README.md`를 공개 포트폴리오 첫 화면용으로 재작성했다.
- [x] `docs/portfolio_draft.md`를 README/이력서/면접 답변의 source document로 정리했다.
- [x] `README.en.md`를 추가해 영문 지원용 요약 README를 만들었다.
- [x] 한국 기업 데이터 엔지니어 제출용 본문 `docs/korean_company_portfolio_submission.md`를 추가했다.
- [x] 제출용 HTML/DOCX export를 생성했다.
- [x] 지원서 입력란용 100자/300자/700자 설명, bullet, 자기소개서 연결 문장을 추가했다.
- [x] 면접 flashcards와 one-pager를 추가했다.
- [x] 이력서 최종 4개 bullet을 별도 문서로 선별했다.

## Decisions

- **한국 기업 제출 형식**: GitHub README만 두지 않고, PDF/DOCX로 변환 가능한 Markdown 제출본 + 채용폼 입력 문구 + 이력서 bullet + 면접 카드 조합으로 구성한다.
- **Claim boundary**: synthetic payment benchmark, 25 labeled campaign rows, AWS target architecture only, `/query/v2` production hardening 미완료를 문서 전반에 명시한다.
- **미구현 항목 처리**: query optimization, locust load test, weekly LLM report DAG, Superset OSS contribution은 완료 주장으로 쓰지 않고 `Not implemented / Stretch`로 분리한다.
- **Export strategy**: 로컬에 `pdflatex`가 없어 PDF export는 보류하고, `pandoc`으로 HTML과 DOCX를 생성한다.

## Files changed

- `README.md` — 공개 포트폴리오용 구조로 재작성, 한국 제출 문서/영문 README/지원서 문구 링크 추가.
- `README.en.md` — 영문 지원용 README 추가.
- `docs/portfolio_draft.md` — 포트폴리오 source 문서로 재정리.
- `docs/portfolio_one_pager.md` — 1-page 요약본 추가.
- `docs/interview_flashcards.md` — 면접 질문 15개와 답변 카드 추가.
- `docs/korean_company_portfolio_submission.md` — 한국 기업 데이터 엔지니어 제출용 포트폴리오 본문 추가.
- `docs/korean_job_application_snippets.md` — 채용 플랫폼 입력란용 문구 추가.
- `docs/resume_selected_bullets_ko.md` — 한국어 이력서 최종 bullet 4개 선별.
- `docs/adinsight_portfolio_submission_ko.html` — 제출용 HTML export.
- `docs/adinsight_portfolio_submission_ko.docx` — 제출용 DOCX export.
- `docs/session_log/README.md` — Session 48 인덱스 추가.
- `CLAUDE.md` — 직전 세션 요약 갱신.
- `docs/daily_log.md` — 포트폴리오 패키징 한 줄 기록 추가.

## Concepts taught

- **한국 기업 포트폴리오 패키지** — README 하나보다 이력서 bullet, PDF/DOCX 제출본, 채용폼 입력 문구, GitHub 증거 링크를 묶는 방식이 더 실무적이다.
- **Claim boundary** — 포트폴리오에서 합성 데이터와 benchmark 결과는 실제 운영 성능처럼 말하지 않고 한계와 함께 제시해야 한다.
- **Evidence-first writing** — 채용 문서는 도구 나열보다 문제, 행동, 수치 결과, 한계를 빠르게 보여줘야 한다.

## Portfolio assets added

- 제출용 문서: `docs/korean_company_portfolio_submission.md`
- Export: `docs/adinsight_portfolio_submission_ko.html`, `docs/adinsight_portfolio_submission_ko.docx`
- 지원서 문구: `docs/korean_job_application_snippets.md`
- 면접 복습: `docs/interview_flashcards.md`
- 요약본: `docs/portfolio_one_pager.md`
- 이력서 최종 bullet: `docs/resume_selected_bullets_ko.md`
- 영문 README: `README.en.md`

## Open questions

- PDF export가 필요하면 `pdflatex`, `tectonic`, `typst`, 또는 브라우저/Word export 방식 중 하나를 선택해야 한다.
- GitHub 공개 전 실제 remote rendering과 이미지 표시를 브라우저에서 확인하면 더 좋다.
- `metrics/run_results.jsonl`의 기존 runtime append는 이번 문서 커밋과 분리할지 별도 판단이 필요하다.

## Metrics

- `git diff --check` → pass
- 주요 Markdown 로컬 링크 check → pass
- stale claim search (`TBD`, `18/18`, `LightGBM`, `ml/`, `query_optimization_log`, `Superset 오픈소스`) → CI badge URL 외 문제 없음
- `pandoc docs/korean_company_portfolio_submission.md --standalone ... -o docs/adinsight_portfolio_submission_ko.html` → success
- `pandoc docs/korean_company_portfolio_submission.md -o docs/adinsight_portfolio_submission_ko.docx` → success
- PDF export attempt → blocked locally because `pdflatex` is not installed

## Next session — start here

1. Commit only portfolio documentation files; keep `metrics/run_results.jsonl` separate unless intentionally committing runtime metrics.
2. If needed, generate PDF from `docs/adinsight_portfolio_submission_ko.docx` using Word/Pages/Google Docs or install a pandoc PDF engine.
3. Before sharing publicly, inspect GitHub-rendered README and verify image rendering for `docs/images/00_architecture.svg` and `docs/images/06_text2sql_demo.gif`.
