SELECT  s.*,
    e.entity,
    e.type,
    e.score,
    t.lang as language,
    coordinates.coordinates[1] AS lon,
    coordinates.coordinates[2] AS lat ,
    place.name,
    place.country,
    (t.timestamp_ms / 1000) + (9 * 60 * 60) AS timestamp_in_seconds,
    regexp_replace(source,
    '\<.+?\>', '') AS src
FROM twitter_timeline_dashboard.tweets t
JOIN twitter_timeline_dashboard.tweet_sentiments s
    ON (s.tweetid = t.id)
JOIN twitter_timeline_dashboard.tweet_entities e
    ON (e.tweetid = t.id) 
