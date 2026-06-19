with creator_summary as (
    select * from {{ ref('mart_creator_sponsored_summary') }}
)

select
    owner_username as creator_username,
    owner_full_name as creator_display_name,

    posts as total_posts,
    sponsored_candidate_posts,
    hidden_likes_posts,
    carousel_posts,
    video_posts,

    avg_likes_count_clean,
    avg_comments_count,
    sponsored_candidate_rate,
    hidden_likes_rate,
    has_engagement_signal,
    included_in_creator_review
from creator_summary
