--
-- =============================================================================
-- 04_synthetic_raw_schema.sql
--
-- ---------------------------------------------------------------------------
-- 목적: Phase 2C 합성/반합성 raw 테이블 정의.
-- 원칙: Apify 실제 관측 post에 synthetic campaign attribution을 붙이되,
--       views/impressions/clicks처럼 현재 수집되지 않는 지표는 만들지 않는다.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.syn_campaigns (
    campaign_id                 TEXT PRIMARY KEY,
    campaign_name               TEXT NOT NULL,
    region                      TEXT NOT NULL,
    category                    TEXT NOT NULL,
    objective                   TEXT NOT NULL,
    campaign_budget_krw         INTEGER NOT NULL,
    start_date                  DATE NOT NULL,
    end_date                    DATE NOT NULL,
    duration_days               INTEGER NOT NULL,
    synthetic_source            TEXT NOT NULL,
    raw_payload                 JSONB NOT NULL,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE raw.syn_campaigns IS
    'Synthetic campaign dimension for Phase 2C campaign-to-payment simulation.';

CREATE INDEX IF NOT EXISTS idx_syn_campaigns_region
    ON raw.syn_campaigns (region);

CREATE INDEX IF NOT EXISTS idx_syn_campaigns_category
    ON raw.syn_campaigns (category);

CREATE INDEX IF NOT EXISTS idx_syn_campaigns_start_date
    ON raw.syn_campaigns (start_date);

CREATE TABLE IF NOT EXISTS raw.syn_post_campaign_attributions (
    post_campaign_attribution_id TEXT PRIMARY KEY,

    post_id                      TEXT NOT NULL REFERENCES raw.ig_posts(id),
    creator_username             TEXT NOT NULL,
    campaign_id                  TEXT NOT NULL REFERENCES raw.syn_campaigns(campaign_id),
    post_date                    DATE NOT NULL,
    source_hashtag               TEXT NOT NULL,
    category                     TEXT NOT NULL,

    likes_count_clean            INTEGER NOT NULL,
    likes_hidden                 BOOLEAN NOT NULL,
    comments_count               INTEGER NOT NULL,
    observed_engagement_count    INTEGER NOT NULL,
    observed_engagement_tier     TEXT NOT NULL,
    paid_partnership_observed    BOOLEAN NOT NULL,

    metric_policy                TEXT NOT NULL,
    synthetic_source             TEXT NOT NULL,
    raw_payload                  JSONB NOT NULL,

    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE raw.syn_post_campaign_attributions IS
    'Actual Apify posts matched to synthetic campaigns using observed likes/comments only.';

CREATE INDEX IF NOT EXISTS idx_syn_post_campaign_attr_post_id
    ON raw.syn_post_campaign_attributions (post_id);

CREATE INDEX IF NOT EXISTS idx_syn_post_campaign_attr_campaign_id
    ON raw.syn_post_campaign_attributions (campaign_id);

CREATE INDEX IF NOT EXISTS idx_syn_post_campaign_attr_post_date
    ON raw.syn_post_campaign_attributions (post_date);

CREATE INDEX IF NOT EXISTS idx_syn_post_campaign_attr_engagement_tier
    ON raw.syn_post_campaign_attributions (observed_engagement_tier);

CREATE TABLE IF NOT EXISTS raw.syn_payment_events (
    payment_event_id             TEXT PRIMARY KEY,

    post_campaign_attribution_id TEXT NOT NULL REFERENCES raw.syn_post_campaign_attributions(post_campaign_attribution_id),
    post_id                      TEXT NOT NULL REFERENCES raw.ig_posts(id),
    campaign_id                  TEXT NOT NULL REFERENCES raw.syn_campaigns(campaign_id),
    creator_username             TEXT NOT NULL,
    event_ts                     TIMESTAMPTZ NOT NULL,

    region                       TEXT NOT NULL,
    category                     TEXT NOT NULL,
    objective                    TEXT NOT NULL,
    currency                     TEXT NOT NULL,
    payment_amount_local         NUMERIC(18, 2) NOT NULL,
    fx_rate_to_krw               NUMERIC(18, 6) NOT NULL,
    payment_amount_krw           NUMERIC(18, 2) NOT NULL,
    is_refunded                  BOOLEAN NOT NULL,

    observed_engagement_count    INTEGER NOT NULL,
    observed_engagement_tier     TEXT NOT NULL,
    campaign_budget_krw          INTEGER NOT NULL,
    paid_partnership_observed    BOOLEAN NOT NULL,
    expected_payment_count       NUMERIC(18, 4) NOT NULL,

    conversion_model             TEXT NOT NULL,
    synthetic_source             TEXT NOT NULL,
    raw_payload                  JSONB NOT NULL,

    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE raw.syn_payment_events IS
    'Synthetic payment events simulated from observed likes/comments engagement and campaign budget.';

CREATE INDEX IF NOT EXISTS idx_syn_payment_events_attribution_id
    ON raw.syn_payment_events (post_campaign_attribution_id);

CREATE INDEX IF NOT EXISTS idx_syn_payment_events_campaign_id
    ON raw.syn_payment_events (campaign_id);

CREATE INDEX IF NOT EXISTS idx_syn_payment_events_event_ts
    ON raw.syn_payment_events (event_ts);

CREATE INDEX IF NOT EXISTS idx_syn_payment_events_engagement_tier
    ON raw.syn_payment_events (observed_engagement_tier);
