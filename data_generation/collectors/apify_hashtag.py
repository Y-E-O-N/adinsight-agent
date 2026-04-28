"""Apify Instagram Hashtag Scraper 를 호출해 해시태그 게시물을 수집하는 모듈."""

import os

from apify_client import ApifyClient

# Apify 마켓플레이스의 공식 Actor 식별자
# 변경 가능성이 있는 값이라 모듈 상수로 분리해 한 곳에서만 관리한다.
ACTOR_ID = "apify/instagram-hashtag-scraper"

def collect_hashtag(hashtag: str, k: int = 20) -> list[dict]:
    """주어진 해시태그의 최근 게시물 k개를 apify를 통해 수집한다.

    Args:
        hashtag: '#'을 제외한 해시태그 문자열
        k: 해시태그 별 수집할 게시물 개수. 기본 20

    Returns:
        Apify Actor 가 반환한 게시물 dict의 리스트.
        스키마는 Actor 응답 그대로 (정제는 호출 측 책임)
    """

    # 환경변수에서 토큰을 읽어 클라이언트 생성.
    # 토큰이 없으면 KeyError가 즉시 발생하도록 의도 (조용한 실패 방지).
    client = ApifyClient(token=os.environ["APIFY_TOKEN"])

    # Actor 입력. instagram-hashtag-scraper는 hashtags 배열을 받는다.
    run_input = {
        "hashtags": [hashtag],
        "resultsLimit": k,
    }

    # actor(...).call(...) 은 "실행시작 + 완료 대기" 를 동기로 처리한다.
    # 반환값 run은 실행 메타데이터 (id, status, defaultDatasetId, ...).
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    # 실행 결과는 Apify Dataset에 저장된다
    # iterate_items() 가 페이징을 자동 처리해 한 건 씩 yield한다.
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items