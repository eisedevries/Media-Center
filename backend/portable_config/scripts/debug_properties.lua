-- Debugging script to list all available properties in mpv
local msg = require 'mp.msg'

local function log_all_properties()
    local properties = {
        "demuxer-cache-state",
        "demuxer-cache-duration",
        "demuxer-bitrate",
        "cache-used",
        "cache",
        "file-pos",
        "seekable-ranges",
        "network-speed",
        "bytes-per-second",
    }

    for _, prop in ipairs(properties) do
        local value = mp.get_property(prop, "N/A")
        msg.info(string.format("Property: %s, Value: %s", prop, value))
    end
end

mp.register_event("file-loaded", log_all_properties)
msg.info("Debugging script loaded. Play a video to see properties.")
