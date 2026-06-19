with stg_posts as (
    select * from {{ ref('stg_ig_posts') }}
),

owner_activity as (
    select
        owner_username,
        max(owner_full_name) as owner_full_name,

        count(*) as posts,
        count(*) filter (where is_sponsored_candidate) as sponsored_candidate_posts,
        count(*) filter (where likes_hidden) as hidden_likes_posts,
        count(*) filter (where is_carousel) as carousel_posts,
        count(*) filter (where is_video) as video_posts,

        avg(likes_count_clean) as avg_likes_count_clean,
        avg(comments_count) as avg_comments_count,

        round(
            count(*) filter (where is_sponsored_candidate)::numeric / nullif(count(*), 0),
            4
        ) as sponsored_candidate_rate,

        round(
            count(*) filter (where likes_hidden)::numeric / nullif(count(*), 0),
            4
        ) as hidden_likes_rate,

        (
            avg(likes_count_clean) is not null
            or avg(comments_count) > 0
        ) as has_engagement_signal
    from stg_posts
    where owner_username is not null
    group by owner_username
)

select * from owner_activity