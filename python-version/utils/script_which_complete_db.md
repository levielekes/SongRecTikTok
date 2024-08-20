1. OR tiktok_sound_last_checked_by_shazam_with_no_result <= current_date - INTERVAL '14 days' 
I modified this interval from 14 to 10, because I got some TikTok Sounds, for example parts of "Eneli - Ileană, Ileană", which should have, but wasn't recognized and didn't have an equivalent song, because it was released in a timeframe of 10 days from the first scan. 10 days seems alright for now, checking each song 3 times per month. Seems to be too rare this way too, but let's find other examples which to prove that.

2. If want to check how progress is running the machines and how many sounds left, run this query:

SELECT 
    sounds_data_tiktoksounds.id
FROM 
    sounds_data_tiktoksounds 
LEFT JOIN 
    sounds_data_shazamsounds 
ON 
    sounds_data_tiktoksounds.shazamsounds_id = sounds_data_shazamsounds.id 
LEFT JOIN (
    SELECT tiktoksounds_id, MAX(date) as max_date
    FROM sounds_data_tiktoksoundidsdailytotalvideocount
    GROUP BY tiktoksounds_id
) latest_v ON sounds_data_tiktoksounds.id = latest_v.tiktoksounds_id
LEFT JOIN sounds_data_tiktoksoundidsdailytotalvideocount 
ON 
    latest_v.tiktoksounds_id = sounds_data_tiktoksoundidsdailytotalvideocount.tiktoksounds_id 
    AND latest_v.max_date = sounds_data_tiktoksoundidsdailytotalvideocount.date
WHERE
    sounds_data_tiktoksounds.tiktok_sound_fetch_shazam_status = 0
    AND sounds_data_tiktoksounds.status = 0
    AND sounds_data_tiktoksounds.shazamsounds_id IS NULL 
    AND (
        sounds_data_tiktoksounds.tiktok_sound_last_checked_by_shazam_with_no_result IS NULL 
        OR sounds_data_tiktoksounds.tiktok_sound_last_checked_by_shazam_with_no_result <= CURRENT_DATE - INTERVAL '10 days'
    )
    AND sounds_data_tiktoksoundidsdailytotalvideocount.tiktok_total_video_count >= 50                                            
ORDER BY RANDOM()