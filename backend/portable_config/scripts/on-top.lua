-- topmost.lua
--
-- This script makes mpv’s window “topmost” when it is in fullscreen mode,
-- ensuring no other window overlays it. Once you switch to a windowed mode,
-- the “always on top” flag is disabled.
--
-- Save this file in your mpv “scripts” directory (for example, ~/.config/mpv/scripts/ on Linux
-- or mpv's installation scripts folder on Windows).

local function update_ontop(_, new_value)
    -- new_value is a boolean indicating whether mpv is in fullscreen mode.
    if new_value then
        mp.set_property_bool("ontop", true)
    else
        mp.set_property_bool("ontop", false)
    end
end

-- Observe changes to the "fullscreen" property.
mp.observe_property("fullscreen", "bool", update_ontop)

-- Run the update function on script load to set the initial state.
local fullscreen = mp.get_property_native("fullscreen")
update_ontop(nil, fullscreen)
