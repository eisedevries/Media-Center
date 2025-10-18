-- MPV Lua Script to map arrow keys for volume control

mp.add_key_binding("UP", "volume_up", function()
    mp.command("add volume 2")
end, {repeatable=true}) -- Allow holding the key

mp.add_key_binding("DOWN", "volume_down", function()
    mp.command("add volume -2")
end, {repeatable=true}) -- Allow holding the key
