with posts as (
    select * from {{ source('raw', 'ig_posts') }}
),

post_sources as (
    select * from {{ source('raw', 'ig_post_sources') }}
)

select
    p.id as post_id,
    p.short_code,
    p.url as post_url,
    p.posted_at as posted_at_utc,
    (p.posted_at at time zone 'UTC')::date as posted_date,

    p.owner_username,
    p.owner_full_name,
    p.owner_id,

    p.caption,
    (p.caption is null or btrim(p.caption) = '') as caption_is_empty,
    regexp_count(coalesce(p.caption, ''), '#[[:alnum:]_가-힣]+') as caption_hashtag_count,
    regexp_count(coalesce(p.caption, ''), '@[A-Za-z0-9._]+') as mention_count,

    p.likes_count as likes_count_raw,
    coalesce(p.likes_count = -1, false) as likes_hidden,
    case
        when p.likes_count = -1 then null
        else p.likes_count
    end as likes_count_clean,
    p.comments_count,

    p.post_type,
    p.product_type,
    (p.post_type = 'Sidecar' or p.product_type = 'carousel_container') as is_carousel,
    (p.post_type = 'Video' or p.product_type = 'clips') as is_video,
    (
        coalesce(p.caption, '') ~* '(광고|협찬|제품제공|제품지원|AD|sponsored|gift)'
    ) as is_sponsored_candidate,

    array_remove(array_agg(s.source_hashtag order by s.source_hashtag), null) as source_hashtags,
    count(distinct s.source_hashtag) as source_hashtag_count,

    p.display_url,
    p.images,
    p.child_posts,
    p.music_info,
    p.raw_payload,
    p.collected_at,
    p.updated_at
from posts p
left join post_sources s
    on s.post_id = p.id
group by
    p.id,
    p.short_code,
    p.url,
    p.posted_at,
    p.owner_username,
    p.owner_full_name,
    p.owner_id,
    p.caption,
    p.likes_count,
    p.comments_count,
    p.post_type,
    p.product_type,
    p.display_url,
    p.images,
    p.child_posts,
    p.music_info,
    p.raw_payload,
    p.collected_at,
    p.updated_at
