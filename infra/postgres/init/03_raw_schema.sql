
--
-- =============================================================================
-- 03_raw_schema.sql
--
-- ---------------------------------------------------------------------------
-- 목적: raw 레이어 스키마 + Instagram 원본 게시물 테이블 정의.
-- 실행 시점: Postgres 컨테이너 최초 기동 시 1회 (init 스크립트).
-- 불변규칙 #1: raw 는 원본 보존. 모든 변환은 staging 이후 dbt 에서.
-- 멱등(idempotent): IF NOT EXISTS / ON CONFLICT 로 재실행 안전.
-- BRIN (Block Range Index) : 시계열용 가벼운 인덱스. B-tree가 행마다 포인터 두는 페이지 범위 (여기선 64페이지)의 min/max 만 저장
-- =============================================================================

-- 1) raw schema 생성 (없으면)
CREATE SCHEMA IF NOT EXISTS raw;

COMMENT ON SCHEMA raw IS
    '원본 보존 레이어. Apify 등 외부 수집 데이터의 1:1 적재처. 변환, 정규화 금지';

-- 2) Instagram 게시물 테이블
CREATE TABLE IF NOT EXISTS raw.ig_posts (
    -- 식별자
    id              TEXT        PRIMARY KEY,    -- Instagram 게시물 ID
    short_code      TEXT,                       -- URL의 마지막 부분
    url             TEXT,                       -- http://www.instagram.com/p/{shortCode}/

    -- 분류
    post_type       TEXT,                       -- Sidecar / Image / Video
    product_type    TEXT,                       -- carousel_container / clips / feed

    -- 본문 지표
    caption         TEXT,                       -- 본문, 해시태그, 멘션은 staging에서 정규식 추출
    comments_count  INTEGER,                    -- 댓글수
    likes_count     INTEGER,                    -- -1 = 좋아요 숨김. NULL 변환은 staging에서
    posted_at       TIMESTAMPTZ,                -- 게시 시각 (UTC)

    -- 크리에이터
    owner_username  TEXT,
    owner_full_name TEXT,
    owner_id        TEXT,                       -- username 변경에도 유지되는 안정 id

    -- 미디어 (구조 보존: JSONB)
    display_url     TEXT,
    images          JSONB,                      -- list[url]
    child_posts     JSONB,                      -- 캐러셀 자식 게시물
    music_info      JSONB,                      -- 릴스 음악 정보

    -- 수집 메타 정보
    raw_payload     JSONB       NOT NULL,       -- 원본 1건 통째로
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(), -- 최초 적재 시각
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()  -- 갱신 시각
);

COMMENT ON TABLE raw.ig_posts IS
    'Apify instagram-hashtag-scraper 응답 1:1 적재. PK=id로 멱등.';

-- 3) 인스타그램 게시물 수집 경로 테이블
CREATE TABLE IF NOT EXISTS raw.ig_post_sources (
    post_id         TEXT        NOT NULL REFERENCES raw.ig_posts(id),
    source_hashtag  TEXT        NOT NULL,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (post_id, source_hashtag)
);

COMMENT ON TABLE raw.ig_post_sources IS
    'Instagram 게시물이 어떤 해시태그 수집에서 발견됐는지 기록하는 lineage 테이블';

-- 4) 인덱스
-- 시계열 핉터용 BRIN: posted_at 은 자연 정렬, BRIN이 페이지 범위 min/max만 저장 -> 인덱스 크기 1/100
CREATE INDEX IF NOT EXISTS idx_ig_posts_posted_at_brin
    ON raw.ig_posts USING BRIN (posted_at) WITH (pages_per_range = 64);

-- 크리에이터 조회
CREATE INDEX IF NOT EXISTS idx_ig_posts_owner_username
    ON raw.ig_posts (owner_username);

-- 시드 추적 (어느 해시태그에서 수집됐는지 분포 확인)
CREATE INDEX IF NOT EXISTS idx_ig_post_source_hashtag
    ON raw.ig_post_sources (source_hashtag);