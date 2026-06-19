with stg_posts as (
    select * from {{ ref('stg_ig_posts') }}
),

source_expanded as (
    select
        unnest(source_hashtags) as source_hashtag,
        post_id,
        owner_username,
        caption_is_empty,
        likes_hidden,
        is_sponsored_candidate,
        likes_count_clean,
        comments_count,
        is_carousel,
        is_video
    from stg_posts
)

select
    source_hashtag,
    count(*) as posts,
    count(distinct post_id) as distinct_posts,
    count(distinct owner_username) as distinct_owners,

    count(*) filter (where caption_is_empty) as empty_caption_posts,
    count(*) filter (where likes_hidden) as hidden_likes_posts,
    count(*) filter (where is_sponsored_candidate) as sponsored_candidate_posts,
    count(*) filter (where is_carousel) as carousel_posts,
    count(*) filter (where is_video) as video_posts,

    round(
        count(*) filter (where caption_is_empty)::numeric / nullif(count(*), 0),
        4
    ) as empty_caption_rate,
    round(
        count(*) filter (where likes_hidden)::numeric / nullif(count(*), 0),
        4
    ) as hidden_likes_rate,
    round(
        count(*) filter (where is_sponsored_candidate)::numeric / nullif(count(*), 0),
        4
    ) as sponsored_candidate_rate,

    avg(likes_count_clean) as avg_likes_count_clean,
    avg(comments_count) as avg_comments_count,

    (count(*) >= 20) as has_minimum_sample,
    (
        count(*) >= 20
        and count(*) filter (where is_sponsored_candidate)::numeric / nullif(count(*), 0) >= 0.3
    ) as useful_for_sponsored_analysis
from source_expanded
group by source_hashtag
