from pathlib import Path
import yaml

import os
import psycopg

QUESTIONS_PATH = Path("agent/eval/text2sql_questions.yml")

def main():
    data = yaml.safe_load(QUESTIONS_PATH.read_text())
    questions = data["questions"]

    passed = 0
    failed = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for question in questions:
                count_sql = build_count_sql(question["expected_sql"])

                cur.execute(count_sql)
                actual_rows = cur.fetchone()[0]
                expected_rows = question["current_result_rows"]

                status = "PASS" if actual_rows == expected_rows else "FAIL"

                if status == "PASS":
                    passed += 1
                else:
                    failed += 1

                print(
                    question["id"],
                    status,
                    f"expected={expected_rows}",
                    f"actual={actual_rows}",
                )

    total = passed + failed
    print(f"summary passed={passed} failed={failed} total={total}")

    if failed > 0:
        raise SystemExit(1)

def build_count_sql(sql: str) -> str:
    return f"""
        select count(*) as actual_rows
        from (
        {sql}
        ) as eval_query
    """.strip()

def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adinsight"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


if __name__== "__main__":
    main()
