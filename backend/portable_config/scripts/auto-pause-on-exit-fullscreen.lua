local mp = require 'mp'


-- Function to unpause after a short delay when entering fullscreen
local function delayed_unpause()
    mp.add_timeout(0.1, function() -- Small delay (prevents accidental pause from double-click)
        mp.set_property("pause", "no")
    end)
end

-- Custom double-click handling: Toggle fullscreen manually
mp.add_key_binding("mbtn_left_dbl", "toggle_fullscreen", function()
    local is_fullscreen = mp.get_property_native("fullscreen")

    if not is_fullscreen then
        -- If entering fullscreen, wait and then unpause the video
        delayed_unpause()
    end

    -- Toggle fullscreen state
    mp.set_property_native("fullscreen", not is_fullscreen)
end)

-- Function to pause playback after a short delay
local function delayed_pause()
    mp.add_timeout(0.1, function() -- Small delay to prevent interference with input events
        mp.set_property("pause", "yes")
    end)
end

-- Auto-pause when exiting fullscreen (with delay)
mp.observe_property("fullscreen", "bool", function(_, is_fullscreen)
    if not is_fullscreen then
        delayed_pause()
    end
end)
