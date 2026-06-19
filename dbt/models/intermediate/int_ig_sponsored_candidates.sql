with stg_posts as (
    select * from {{ ref('stg_ig_posts') }}
),

sponsored_candidates as (
    select
        post_id,
        short_code,
        post_url,
        posted_at_utc,
        posted_date,

        owner_username,
        owner_full_name,

        caption,
        likes_hidden,
        likes_count_clean,
        comments_count,

        coalesce(likes_count_clean, 0) + coalesce(comments_count, 0) as engagement_count,
        (
            likes_count_clean is not NULL
            or coalesce(comments_count, 0) > 0
        ) as has_engagement_signal,

        is_carousel,
        is_video,

        source_hashtags,
        source_hashtag_count,

        case
            when coalesce(caption, '') ~* '(제품제공|제품지원|gift)' then 'product_provided'
            when coalesce(caption, '') ~* '(광고|협찬|AD|sponsored)' then 'ad_disclosure'
            else 'other_keyword'
        end as sponsored_keyword_group
    from stg_posts
    where is_sponsored_candidate
)

select * from sponsored_candidates