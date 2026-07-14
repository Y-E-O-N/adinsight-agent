# Stage 6 Text2SQL Failure Improvement Model

작성일: 2026-07-09

이 문서는 lightweight eval failure와 strict eval failure를 함께 보고,
가장 많은 실패를 줄일 가능성이 큰 schema/prompt/validator 개선 액션을 우선순위화한다.

## Improvement Actions

| Priority | Affected cases | Affected models | Recommendation |
|---:|---:|---:|---|
| 1 | 18 | 4 | Fix schema context columns and add expected output-column examples. |
| 2 | 13 | 4 | Add required SQL feature examples and validator-aligned constraints. |
| 3 | 11 | 4 | Add ordering and top-row priority examples for this question family. |
| 4 | 9 | 4 | Tighten LIMIT policy and preserve explicit Top N or expected broad-list limit. |
| 5 | 3 | 3 | Inspect generated SQL and add the smallest schema or prompt example that covers it. |
| 6 | 2 | 3 | Add objective to prediction monitor schema context and few-shot examples. |
| 7 | 2 | 2 | Strengthen refusal policy for ambiguous or unsafe questions without echoing terms. |
| 8 | 2 | 1 | Add canonical join examples for prediction monitor and campaign ROI tier questions. |
| 9 | 2 | 1 | Clarify answerability in schema context; this question is in-domain. |

## Evidence By Action

### 1. Fix schema context columns and add expected output-column examples.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | strict | `p4_q001` | `FAIL` | `missing_expected_columns` | Which creators should we review first for sponsored content? |
| Gemini gemini-3.1-flash-lite | strict | `p4_q003` | `FAIL` | `missing_expected_columns` | Which influencers have the top 10 sponsored candidate rates? |
| Gemini gemini-3.1-flash-lite | strict | `p4_q006` | `FAIL` | `missing_expected_columns` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Gemini gemini-3.1-flash-lite | strict | `p4_q007` | `FAIL` | `missing_expected_columns` | List the top 10 creators where likes are often hidden. |
| Gemini gemini-3.1-flash-lite | strict | `p4_q009` | `FAIL` | `missing_expected_columns` | Show the first 20 creators that have engagement signals available. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q002` | `FAIL` | `missing_expected_columns` | Show average ROAS and net payment amount by campaign objective. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q004` | `FAIL` | `missing_expected_columns` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q010` | `FAIL` | `missing_expected_columns` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q011` | `FAIL` | `missing_expected_columns` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q012` | `FAIL` | `missing_expected_columns` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q014` | `FAIL` | `missing_expected_columns` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |
| Ollama phi4:14b | strict | `p4_q001` | `FAIL` | `missing_expected_columns` | Which creators should we review first for sponsored content? |
| Ollama phi4:14b | strict | `p4_q003` | `FAIL` | `missing_expected_columns` | Which influencers have the top 10 sponsored candidate rates? |
| Ollama phi4:14b | strict | `p4_q006` | `FAIL` | `missing_expected_columns` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Ollama phi4:14b | strict | `p4_q009` | `FAIL` | `missing_expected_columns` | Show the first 20 creators that have engagement signals available. |
| Ollama phi4:14b | strict | `p4_q010` | `FAIL` | `missing_expected_columns` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Ollama phi4:14b | strict | `p5_q002` | `FAIL` | `missing_expected_columns` | Show average ROAS and net payment amount by campaign objective. |
| Ollama phi4:14b | strict | `p5_q003` | `FAIL` | `missing_expected_columns` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| Ollama phi4:14b | strict | `p5_q004` | `FAIL` | `missing_expected_columns` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Ollama phi4:14b | strict | `p5_q005` | `FAIL` | `missing_expected_columns` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| Ollama phi4:14b | lightweight | `p5_q007` | `FAIL` | `schema_context_columns` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Ollama phi4:14b | strict | `p5_q008` | `FAIL` | `missing_expected_columns` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. |
| Ollama phi4:14b | strict | `p5_q010` | `FAIL` | `missing_expected_columns` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |
| Ollama phi4:14b | lightweight | `p5_q012` | `FAIL` | `schema_context_columns` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p4_q003` | `FAIL` | `missing_expected_columns` | Which influencers have the top 10 sponsored candidate rates? |
| Ollama qwen2.5-coder:7b | strict | `p4_q005` | `FAIL` | `missing_expected_columns` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Ollama qwen2.5-coder:7b | strict | `p4_q006` | `FAIL` | `missing_expected_columns` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p4_q007` | `FAIL` | `missing_expected_columns` | List the top 10 creators where likes are often hidden. |
| Ollama qwen2.5-coder:7b | strict | `p4_q008` | `FAIL` | `missing_expected_columns` | 평균 댓글 수가 높은 인플루언서 Top 10을 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p4_q009` | `FAIL` | `missing_expected_columns` | Show the first 20 creators that have engagement signals available. |
| Ollama qwen2.5-coder:7b | strict | `p5_q002` | `FAIL` | `missing_expected_columns` | Show average ROAS and net payment amount by campaign objective. |
| Ollama qwen2.5-coder:7b | strict | `p5_q003` | `FAIL` | `missing_expected_columns` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q005` | `FAIL` | `missing_expected_columns` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q007` | `FAIL` | `schema_context_columns` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Ollama qwen2.5-coder:7b | strict | `p5_q008` | `FAIL` | `missing_expected_columns` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q011` | `FAIL` | `missing_expected_columns` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q012` | `FAIL` | `schema_context_columns` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q014` | `FAIL` | `schema_context_columns` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q001` | `FAIL` | `missing_expected_columns` | Which creators should we review first for sponsored content? |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q003` | `FAIL` | `missing_expected_columns` | Which influencers have the top 10 sponsored candidate rates? |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q006` | `FAIL` | `missing_expected_columns` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q002` | `FAIL` | `missing_expected_columns` | Show average ROAS and net payment amount by campaign objective. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q008` | `FAIL` | `missing_expected_columns` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q010` | `FAIL` | `missing_expected_columns` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |

### 2. Add required SQL feature examples and validator-aligned constraints.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | strict | `p5_q001` | `FAIL` | `missing_required_sql_feature` | Which campaigns have the highest ROAS? |
| Gemini gemini-3.1-flash-lite | strict | `p5_q003` | `FAIL` | `missing_required_sql_feature` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q005` | `FAIL` | `missing_required_sql_feature` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| Gemini gemini-3.1-flash-lite | strict | `p5_q006` | `FAIL` | `missing_required_sql_feature` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q009` | `BLOCKED` | `validator_blocked` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama phi4:14b | strict | `p5_q006` | `FAIL` | `missing_required_sql_feature` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| Ollama phi4:14b | strict | `p5_q009` | `BLOCKED` | `validator_blocked` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama phi4:14b | strict | `p5_q011` | `FAIL` | `missing_required_sql_feature` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| Ollama phi4:14b | strict | `p5_q014` | `FAIL` | `missing_required_sql_feature` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |
| Ollama qwen2.5-coder:7b | strict | `p4_q001` | `FAIL` | `missing_required_sql_feature` | Which creators should we review first for sponsored content? |
| Ollama qwen2.5-coder:7b | strict | `p4_q004` | `FAIL` | `missing_required_sql_feature` | 협찬 후보 게시물이 있는 크리에이터 상위 20명을 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p4_q010` | `FAIL` | `missing_required_sql_feature` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q004` | `FAIL` | `missing_required_sql_feature` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q006` | `FAIL` | `missing_required_sql_feature` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q010` | `FAIL` | `missing_required_sql_feature` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q010` | `BLOCKED` | `validator_blocked` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q003` | `FAIL` | `missing_required_sql_feature` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q005` | `FAIL` | `missing_required_sql_feature` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q006` | `FAIL` | `missing_required_sql_feature` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q013` | `BLOCKED` | `validator_blocked` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |

### 3. Add ordering and top-row priority examples for this question family.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q002` | `FAIL` | `semantic_ordering` | Show the top 20 creators with at least one sponsored candidate post. |
| Gemini gemini-3.1-flash-lite | strict | `p4_q002` | `FAIL` | `result_set_mismatch` | Show the top 20 creators with at least one sponsored candidate post. |
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q003` | `FAIL` | `semantic_ordering` | Which influencers have the top 10 sponsored candidate rates? |
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q005` | `FAIL` | `semantic_ordering` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Gemini gemini-3.1-flash-lite | strict | `p4_q005` | `FAIL` | `result_set_mismatch` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q006` | `FAIL` | `semantic_ordering` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q014` | `FAIL` | `semantic_ordering` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |
| Ollama phi4:14b | strict | `p4_q002` | `FAIL` | `result_set_mismatch` | Show the top 20 creators with at least one sponsored candidate post. |
| Ollama phi4:14b | lightweight | `p4_q004` | `FAIL` | `semantic_ordering` | 협찬 후보 게시물이 있는 크리에이터 상위 20명을 보여줘. |
| Ollama phi4:14b | strict | `p4_q004` | `FAIL` | `result_set_mismatch` | 협찬 후보 게시물이 있는 크리에이터 상위 20명을 보여줘. |
| Ollama phi4:14b | lightweight | `p4_q005` | `FAIL` | `semantic_ordering` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Ollama phi4:14b | strict | `p4_q005` | `FAIL` | `result_set_mismatch` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Ollama phi4:14b | lightweight | `p4_q006` | `FAIL` | `semantic_ordering` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Ollama phi4:14b | strict | `p4_q007` | `FAIL` | `result_set_mismatch` | List the top 10 creators where likes are often hidden. |
| Ollama qwen2.5-coder:7b | strict | `p4_q002` | `FAIL` | `result_set_mismatch` | Show the top 20 creators with at least one sponsored candidate post. |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q003` | `FAIL` | `semantic_ordering` | Which influencers have the top 10 sponsored candidate rates? |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q005` | `FAIL` | `semantic_ordering` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q006` | `FAIL` | `semantic_ordering` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q007` | `FAIL` | `semantic_ordering` | List the top 10 creators where likes are often hidden. |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q009` | `FAIL` | `semantic_ordering` | Show the first 20 creators that have engagement signals available. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q009` | `FAIL` | `semantic_ordering` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama qwen2.5-coder:7b | strict | `p5_q009` | `FAIL` | `result_set_mismatch` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q010` | `FAIL` | `semantic_ordering` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q011` | `FAIL` | `semantic_ordering` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q002` | `FAIL` | `result_set_mismatch` | Show the top 20 creators with at least one sponsored candidate post. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q004` | `FAIL` | `result_set_mismatch` | 협찬 후보 게시물이 있는 크리에이터 상위 20명을 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p4_q005` | `FAIL` | `semantic_ordering` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q005` | `FAIL` | `result_set_mismatch` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p4_q006` | `FAIL` | `semantic_ordering` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p4_q009` | `FAIL` | `semantic_ordering` | Show the first 20 creators that have engagement signals available. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p4_q009` | `FAIL` | `result_set_mismatch` | Show the first 20 creators that have engagement signals available. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q009` | `FAIL` | `semantic_ordering` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q009` | `FAIL` | `result_set_mismatch` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q010` | `FAIL` | `semantic_ordering` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q011` | `FAIL` | `semantic_ordering` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q011` | `FAIL` | `result_set_mismatch` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q014` | `FAIL` | `semantic_ordering` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q014` | `FAIL` | `result_set_mismatch` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |

### 4. Tighten LIMIT policy and preserve explicit Top N or expected broad-list limit.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q001` | `FAIL` | `limit_policy` | Which creators should we review first for sponsored content? |
| Gemini gemini-3.1-flash-lite | lightweight | `p4_q010` | `FAIL` | `limit_policy` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Gemini gemini-3.1-flash-lite | strict | `p4_q010` | `FAIL` | `row_count_mismatch` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q001` | `FAIL` | `limit_policy` | Which campaigns have the highest ROAS? |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q003` | `FAIL` | `limit_policy` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q004` | `FAIL` | `limit_policy` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q005` | `FAIL` | `limit_policy` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q009` | `BLOCKED` | `limit_policy` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama phi4:14b | lightweight | `p4_q001` | `FAIL` | `limit_policy` | Which creators should we review first for sponsored content? |
| Ollama phi4:14b | lightweight | `p4_q010` | `FAIL` | `limit_policy` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Ollama phi4:14b | lightweight | `p5_q004` | `FAIL` | `limit_policy` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Ollama phi4:14b | lightweight | `p5_q006` | `FAIL` | `limit_policy` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| Ollama phi4:14b | lightweight | `p5_q009` | `BLOCKED` | `limit_policy` | Compare campaign count and average ROAS by objective and ROAS performance tier. |
| Ollama phi4:14b | lightweight | `p5_q013` | `FAIL` | `row_count_mismatch` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q001` | `FAIL` | `limit_policy` | Which creators should we review first for sponsored content? |
| Ollama qwen2.5-coder:7b | lightweight | `p4_q010` | `FAIL` | `limit_policy` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q004` | `FAIL` | `limit_policy` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q006` | `FAIL` | `limit_policy` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| Ollama qwen2.5-coder:7b | lightweight | `p5_q013` | `FAIL` | `row_count_mismatch` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p4_q001` | `FAIL` | `limit_policy` | Which creators should we review first for sponsored content? |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p4_q010` | `BLOCKED` | `limit_policy` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q003` | `FAIL` | `limit_policy` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q004` | `FAIL` | `limit_policy` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q004` | `FAIL` | `row_count_mismatch` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q005` | `FAIL` | `limit_policy` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q006` | `FAIL` | `limit_policy` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q013` | `BLOCKED` | `limit_policy` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |

### 5. Inspect generated SQL and add the smallest schema or prompt example that covers it.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q008` | `FAIL` | `provider_error` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q008` | `FAIL` | `no_generated_sql` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. |
| Ollama phi4:14b | strict | `p5_q013` | `FAIL` | `no_generated_sql` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |
| Ollama qwen2.5-coder:7b | strict | `p5_q013` | `FAIL` | `no_generated_sql` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? |
| Ollama qwen2.5-coder:7b | strict | `p5_q014` | `FAIL` | `no_generated_sql` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |

### 6. Add objective to prediction monitor schema context and few-shot examples.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | lightweight | `p5_q007` | `FAIL` | `provider_error` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Gemini gemini-3.1-flash-lite | strict | `p5_q007` | `FAIL` | `no_generated_sql` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Ollama phi4:14b | strict | `p5_q007` | `FAIL` | `no_generated_sql` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Ollama phi4:14b | strict | `p5_q012` | `FAIL` | `no_generated_sql` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |
| Ollama qwen2.5-coder:7b | strict | `p5_q007` | `FAIL` | `no_generated_sql` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| Ollama qwen2.5-coder:7b | strict | `p5_q012` | `FAIL` | `no_generated_sql` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |

### 7. Strengthen refusal policy for ambiguous or unsafe questions without echoing terms.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Gemini gemini-3.1-flash-lite | negative | `neg_q007` | `FAIL_EXECUTED` | `negative_executed` | Who is the best creator? |
| Gemini gemini-3.1-flash-lite | negative | `neg_q011` | `FAIL_UNSAFE_ECHO` | `unsafe_echo` | Find creators related to sexually explicit content. |
| Ollama qwen2.5-coder:7b | negative | `neg_q007` | `FAIL_EXECUTED` | `negative_executed` | Who is the best creator? |

### 8. Add canonical join examples for prediction monitor and campaign ROI tier questions.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| Ollama phi4:14b | lightweight | `p5_q011` | `FAIL` | `join_pattern` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. |
| Ollama phi4:14b | lightweight | `p5_q014` | `FAIL` | `join_pattern` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. |

### 9. Clarify answerability in schema context; this question is in-domain.

| Model | Source | Case | Status | Failure type | Question |
|---|---|---|---|---|---|
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q007` | `REFUSED` | `answerable_refused` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q007` | `REFUSED` | `answerable_refused` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. |
| OpenAI gpt-5.4-mini-2026-03-17 | lightweight | `p5_q012` | `REFUSED` | `answerable_refused` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |
| OpenAI gpt-5.4-mini-2026-03-17 | strict | `p5_q012` | `REFUSED` | `answerable_refused` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. |

## How To Use

1. Fix the highest-priority schema/prompt action.
2. Re-run lightweight eval and strict eval on the same generated SQL artifact.
3. Compare whether affected cases moved from FAIL/BLOCKED/REFUSED to PASS.
4. Only then compare models again.

## Known Limitations

- This model is a deterministic failure-to-action mapping, not a learned ML model.
- It prioritizes high-coverage fixes; it does not prove that each fix will make every listed case pass.
- It depends on strict eval artifacts being present in the same input directory.
