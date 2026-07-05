# Stage 6 Text2SQL v2 Failure Cases

**작성일**: 2026-07-05
**상태**: v2 mock coverage expansion evidence

## Summary

Latest v2 mock eval:

| Mode | Total | PASS | FAIL | REFUSED | BLOCKED | Exec Acc | Refuse Rate | Unsafe Block Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `llm_generated_sql_v2_mock` | 18 | 13 | 0 | 5 | 0 | 1.0000 answerable-only | 0.2778 | 0.0000 |

## Failure Case 1 — Broad No-LIMIT Creator List

- Question id: `p4_q004`
- Question: `협찬 후보 게시물이 있는 크리에이터를 보여줘.`
- Observed during expansion: `BLOCKED`
- Cause: generated SQL selected a non-aggregate creator list without `LIMIT`.
- Decision: leave this question `REFUSED` in mock v2 until the prompt/provider can safely add a bounded limit or pagination contract.

This is desirable behavior: the validator blocks broad generated SQL instead of allowing an unbounded BI query.

## Failure Case 2 — Broad Review Target List

- Question id: `p4_q006`
- Question: `우선 검토 대상 크리에이터만 보여줘.`
- Current status: `REFUSED`
- Cause: expected SQL returns a broad ordered list without explicit limit.
- Next fix: add a user-visible bounded variant such as "Top 50 review targets" or extend the response schema with pagination.

## Failure Case 3 — Engagement Availability Scan

- Question id: `p4_q009`
- Question: `Which creators have engagement signals available?`
- Current status: `REFUSED`
- Cause: broad boolean-filter list without explicit limit.
- Next fix: decide whether v2 should answer with a count/summary or require a bounded list.

## Current Rule

For v2 generated SQL, broad non-aggregate lists should either:

- include an explicit `LIMIT`, or
- be refused until pagination is implemented.
