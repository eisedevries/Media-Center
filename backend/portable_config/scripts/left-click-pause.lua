-- Add left-click to toggle pause
mp.add_key_binding("mbtn_left", "toggle_pause", function()
    mp.command("cycle pause") -- Toggle pause state
end)
