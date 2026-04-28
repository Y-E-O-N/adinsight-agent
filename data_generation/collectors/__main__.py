"""data_generation.collectors 패키지의 로컬 실행 진입점.

사용 예:
    uv run python -m data_generation.collectors --hashtag 다이소화장품 --k 20
"""

import argparse
import json

from data_generation.collectors.apify_hashtag import collect_hashtag


def main() -> None:
    """커맨드라인 인자를 파싱해 collect_hashtag를 실행하고 요약 출력."""
    parser = argparse.ArgumentParser(
        description="Apify로 인스타그램 해시태그 게시물 수집",
    )
    parser.add_argument(
        "--hashtag",
        required=True,
        help="'#'을 제외한 해시태그",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=20,
        help="수집할 게시물 개수 (기본 20)",
    )
    args = parser.parse_args()

    print(f"수집 시작 : hashtag={args.hashtag}, k={args.k}")
    items = collect_hashtag(args.hashtag, args.k)
    print(f"수집 완료 : {len(items)} 건")

    # 첫 게시물 1건의 전체 구조를 보기 좋게 출력 (스키마 파악용).
    if items:
        print("\n--- 첫 게시물 샘플 (JSON) ---")
        print(json.dumps(items[0], ensure_ascii=False, indent=2, default=str))

    # 나머지 4건은 핵심 필드만 짧게.
    print("\n--- 다음 4건 핵심 필드 ---")
    for item in items[1:5]:
        print(
            item.get("ownerUsername"),
            item.get("likesCount"),
            (item.get("caption") or "")[:40],
        )


if __name__ == "__main__":
    main()