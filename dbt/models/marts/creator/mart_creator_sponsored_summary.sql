with owner_activity as (
    select * from {{ ref('int_ig_owner_activity') }}
)

select
    owner_username,
    owner_full_name,

    posts,
    sponsored_candidate_posts,
    hidden_likes_posts,
    carousel_posts,
    video_posts,

    avg_likes_count_clean,
    avg_comments_count,
    sponsored_candidate_rate,
    hidden_likes_rate,
    has_engagement_signal,

    (
        posts >= 2
        or sponsored_candidate_posts >= 1
    ) as included_in_creator_review
from owner_activity