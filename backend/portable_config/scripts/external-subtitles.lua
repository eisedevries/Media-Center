-- prefer-external-subs.lua
-- Automatically prefer external subtitle tracks in MPV

mp.register_event("file-loaded", function()
    local tracks = mp.get_property_native("track-list", {})
    local last_external_sub = nil

    for _, track in ipairs(tracks) do
        if track.type == "sub" and track.external then
            last_external_sub = track.id  -- 1-based ID used by MPV
        end
    end

    if last_external_sub then
        mp.set_property_number("sid", last_external_sub)
        mp.osd_message("Selected external subtitle (track " .. last_external_sub .. ")")
    else
        -- mp.osd_message("No external subtitles found") -- Optional: notify if no external subs are found
    end
end)
